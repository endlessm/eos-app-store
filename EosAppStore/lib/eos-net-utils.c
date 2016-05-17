/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include <glib.h>
#include <glib/gstdio.h>
#include <glib/gi18n-lib.h>

#include <libsoup/soup.h>

#include "eos-app-log.h"
#include "eos-app-utils.h"
#include "eos-net-utils-private.h"

/* Amount of seconds before a downloaded file is considered stale */
#define DOWNLOADED_FILE_STALE_THRESHOLD 3600

/* Amount of seconds that we should keep retrying to download the file after
 * first interruption
 */
#define MAX_DOWNLOAD_RETRY_PERIOD 20

/* Amount of seconds that we should wait before retrying a failed download */
#define DOWNLOAD_RETRY_PERIOD 4

#define GET_DATA_BLOCK_SIZE     64 * 1024

G_DEFINE_QUARK (eos-net-utils-error-quark, eos_net_utils_error)

#if !SOUP_CHECK_VERSION (2, 52, 0)
/* We need these because libsoup version prior to 2.52
 * do not come with autoptr macros
 */
G_DEFINE_AUTOPTR_CLEANUP_FUNC (SoupSession, g_object_unref)
G_DEFINE_AUTOPTR_CLEANUP_FUNC (SoupRequest, g_object_unref)
G_DEFINE_AUTOPTR_CLEANUP_FUNC (SoupMessage, g_object_unref)
G_DEFINE_AUTOPTR_CLEANUP_FUNC (SoupURI, soup_uri_free)
#endif

typedef void (* EosChunkFunc) (GByteArray *chunk,
                               goffset     chunk_len,
                               goffset     bytes_read,
                               gpointer    chunk_func_user_data);

typedef struct {
  goffset                total_len;
  GFileProgressCallback  progress_func;
  gpointer               user_data;
} EosDownloadFileClosure;

static GInputStream *
set_up_download_from_request (SoupRequest   *request,
                              const char    *target_file,
                              GCancellable  *cancellable,
                              GError       **error)
{
  GError *internal_error = NULL;
  GInputStream *in_stream = soup_request_send (request, cancellable, &internal_error);

  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Soup request sending had an internal error: %s",
                                 internal_error->message);

      g_propagate_error (error, internal_error);
      return NULL;
    }

  /* Request twice the size in order to leave some additional room */
  goffset total = soup_request_get_content_length (request) * 2;

  /* Check the target directory by using the parent of the target file path */
  g_autoptr(GFile) tmp = g_file_new_for_path (target_file);
  g_autoptr(GFile) target_dir = g_file_get_parent (tmp);

  if (!eos_check_available_space (target_dir, total, cancellable, &internal_error))
    {
      eos_app_log_error_message ("Not enough space on FS - canceling download");

      g_propagate_error (error, internal_error);
      g_clear_object (&in_stream);
    }

  return in_stream;
}

static gboolean
check_cached_file (const char *target_file,
                   char      **buffer)
{
  struct stat buf;
  if (stat (target_file, &buf) != 0)
    return FALSE;

  GNetworkMonitor *monitor = g_network_monitor_get_default ();
  gboolean network_available = g_network_monitor_get_network_available (monitor);

  time_t now = time (NULL);

  eos_app_log_debug_message ("Checking if the cached file is still good (now: %ld, mtime: %ld, diff: %ld)",
                             now, buf.st_mtime, (now - buf.st_mtime));

  /* We don't want to use cache if we have the network and the cached
   * file is stale.
   */
  if (network_available && (now - buf.st_mtime > DOWNLOADED_FILE_STALE_THRESHOLD))
    {
      eos_app_log_info_message ("Stale file and we have network. "
                                "Not using cached version");
      return FALSE;
    }

  /* If we have a future date set on the file, something is really
   * wrong and if we have the network, don't use it.
   */
  if (network_available && (now - buf.st_mtime < 0))
    {
      eos_app_log_error_message ("File has future date set. "
                                 "We can't use the cached version");
      return FALSE;
    }

  if (network_available)
    eos_app_log_info_message ("Requested file '%s' is within cache allowance.",
                              target_file);
  else
    eos_app_log_info_message ("No network available, using cached file");

  if (buffer)
    {
      GError *internal_error = NULL;
      if (!g_file_get_contents (target_file, buffer, NULL, &internal_error))
        {
          /* Fall through, and re-download the file */
          eos_app_log_error_message ("Could not read cached file '%s': %s",
                                     target_file,
                                     internal_error->message);
          g_clear_error (&internal_error);
          return FALSE;
        }
    }

  return TRUE;
}

static void
download_file_chunk_func (GByteArray *chunk,
                          goffset     chunk_len,
                          goffset     bytes_read,
                          gpointer    chunk_func_user_data)
{
  GByteArray *all_content = chunk_func_user_data;
  guint8 *buffer;

  buffer = (guint8 *) g_strndup ((const char *) chunk->data, chunk_len);
  g_byte_array_append (all_content, buffer, chunk_len);
}

static gboolean
download_file_chunks (GInputStream   *in_stream,
                      GOutputStream  *out_stream,
                      goffset         offset,
                      goffset        *bytes_read,
                      EosChunkFunc    chunk_func,
                      gpointer        chunk_func_user_data,
                      GCancellable   *cancellable,
                      GError        **error)
{
  gboolean retval = FALSE;
  gssize res = 0;
  goffset pos = 0;

  eos_app_log_info_message ("Downloading file chunks start");

  g_autoptr(GByteArray) content = g_byte_array_sized_new (GET_DATA_BLOCK_SIZE);

  /* we don't use splice() because the data is coming from a network
   * request, so it won't have a file descriptor we can use splice()
   * on.
   */
  GError *internal_error = NULL;
  while (!g_cancellable_is_cancelled (cancellable) &&
         (res = g_input_stream_read (in_stream, content->data,
                                     GET_DATA_BLOCK_SIZE,
                                     cancellable, &internal_error)) > 0)
    {
      g_output_stream_write (G_OUTPUT_STREAM (out_stream), content->data, res,
                             cancellable,
                             &internal_error);
      if (internal_error != NULL)
        {
          eos_app_log_error_message ("Downloading file failed. %s",
                                     internal_error->message);
          g_propagate_error (error, internal_error);
          goto out;
        }

      pos += res;

      if (chunk_func != NULL)
        chunk_func (content, res, offset + pos, chunk_func_user_data);
    }

  /* Check for cancellations */
  /* XXX: Since we pass the same cancellable to reading/writing fuctions
   *      we need to check the cancellable status before checking the retval
   *      from reads.
   */
  if (g_cancellable_is_cancelled (cancellable))
    {
      eos_app_log_info_message ("Download cancelled");
      goto out;
    }

  /* Check for errors */
  if (res < 0)
    {
      g_propagate_error (error, internal_error);
      goto out;
    }

  retval = TRUE;

  eos_app_log_info_message ("Exiting download method normally");

out:
  if (bytes_read != NULL)
    *bytes_read = pos;

  return retval;
}

static SoupRequest *
prepare_soup_request (SoupSession  *session,
                      const char   *source_uri,
                      const char   *content_type,
                      GError      **error)
{
  g_autoptr(SoupURI) uri = soup_uri_new (source_uri);

  if (uri == NULL)
    {
      eos_app_log_error_message ("Soup URI is NULL - canceling download");

      g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                           EOS_NET_UTILS_ERROR_INVALID_URL,
                           "No URI provided - cancelling download");

      return NULL;
    }

  GError *internal_error = NULL;
  SoupRequest *request = soup_session_request_uri (session, uri, &internal_error);

  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Soup request had an internal error: %s",
                                 internal_error->message);

      if (g_type_is_a (G_OBJECT_TYPE (request), SOUP_TYPE_REQUEST_HTTP) &&
          g_error_matches (internal_error, G_TLS_ERROR, G_TLS_ERROR_BAD_CERTIFICATE))
        {
          g_autoptr(SoupMessage) message =
            soup_request_http_get_message (SOUP_REQUEST_HTTP (request));

          GTlsCertificateFlags cert_flags = 0;

          g_object_get (message, "tls-errors", &cert_flags, NULL);

          const char *msg;

          if ((cert_flags & G_TLS_CERTIFICATE_EXPIRED) != 0)
            msg = _("The certificate of the target server is expired");
          else if ((cert_flags & G_TLS_CERTIFICATE_REVOKED) != 0)
            msg = _("The certificate of the target server has been revoked");
          else if ((cert_flags & G_TLS_CERTIFICATE_BAD_IDENTITY) != 0)
            msg = _("The certificate of the target server has a bad identity");
          else if ((cert_flags & G_TLS_CERTIFICATE_UNKNOWN_CA) != 0)
            msg = _("The certificate of the target server is from an unknown authority");
          else
            msg = _("The certificate of the target server is bad or invalid");

          g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                               EOS_NET_UTILS_ERROR_BAD_CERTIFICATE,
                               msg);
          g_error_free (internal_error);
        }
      else
        g_propagate_error (error, internal_error);

      return NULL;
    }

  if (content_type != NULL)
    {
      g_autoptr(SoupMessage) message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));
      if (message != NULL)
        soup_message_headers_append (message->request_headers, "Accept", content_type);
    }

  return request;
}

static GOutputStream *
prepare_out_stream (const char    *target_file,
                    const gboolean is_resumed,
                    GCancellable  *cancellable,
                    GError       **error)
{
  GError *internal_error = NULL;
  GFileOutputStream *out_stream = NULL;

  /* If we are not allowed resuming, the resume file is not there, or
   * the server returned a strange status code, we need to start from
   * scratch to ensure that we don't leave junk around
   */
  if (!is_resumed)
    {
      eos_app_log_debug_message ("File is not resumed. Truncating");

      /* we don't use GFile API because the error handling is weird,
       * and we also know that the target is a local file, so there
       * is no point in going through the abstraction
       */
      g_unlink (target_file);
    }

  g_autoptr(GFile) file = g_file_new_for_path (target_file);
  out_stream = g_file_append_to (file, G_FILE_CREATE_NONE, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Opening output file failed: %s. "
                                 "Canceling download", internal_error->message);

      g_set_error (error, EOS_NET_UTILS_ERROR,
                   EOS_NET_UTILS_ERROR_FAILED,
                   _("Could not save the app - "
                     "canceling download (%s)"),
                   internal_error->message);

      g_error_free (internal_error);
    }

  return G_OUTPUT_STREAM (out_stream);
}

static gboolean
prepare_soup_resume_request (SoupRequest  *request,
                             const char   *target_file,
                             gboolean     *needs_download,
                             goffset      *resume_offset,
                             GCancellable *cancellable)
{
  eos_app_log_debug_message ("Getting local file length");

  /* Always assume we start from 0 */
  if (resume_offset != NULL)
    *resume_offset = 0;

  if (needs_download != NULL)
    *needs_download = TRUE;

  g_autoptr(GError) error = NULL;
  g_autoptr(GFile) file = g_file_new_for_path (target_file);
  g_autoptr(GFileInfo) info = g_file_query_info (file, G_FILE_ATTRIBUTE_STANDARD_SIZE,
                                                 G_FILE_QUERY_INFO_NOFOLLOW_SYMLINKS,
                                                 cancellable,
                                                 &error);
  if (error)
    {
      eos_app_log_info_message ("Cannot resume - unable to get "
                                "local file's size (%s: %s).",
                                target_file,
                                error->message);
      return FALSE;
    }

  guint64 size = g_file_info_get_attribute_uint64 (info,
                                                   G_FILE_ATTRIBUTE_STANDARD_SIZE);

  /* Get the total size of the file */
  g_autoptr(GInputStream) stream = soup_request_send (request, cancellable, &error);

  if (error != NULL)
    {
      eos_app_log_error_message ("Soup request sending had an internal error: %s. "
                                 "Will proceed without resuming", error->message);
      return FALSE;
    }

  goffset total = soup_request_get_content_length (request);
  if (total == size)
    {
      /* We already downloaded this */
      if (needs_download != NULL)
        *needs_download = FALSE;
      return TRUE;
    }

  /* Something is not right - download the file again */
  if (total < size)
    return FALSE;

  eos_app_log_info_message ("Resuming %s from offset %" G_GUINT64_FORMAT,
                            target_file,
                            size);

  g_autoptr(SoupMessage) message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));

  if (message == NULL)
    {
      eos_app_log_error_message ("Could not apply header to SOUP message");
      return FALSE;
    }

  /* -1 for end range is to make sure that libsoup doesn't include the
   * end number or the server will reject the message range and return
   * a 206. See github.com/endlessm/eos-shell/issues/4596#issuecomment-111574913
   * for more info
   */
  soup_message_headers_set_range (message->request_headers, size, -1);

  /* If we get to here, we're set on using the partial download */
  if (resume_offset != NULL)
    *resume_offset = size;

  return TRUE;
}

static void
send_progress (GFileProgressCallback  progress_func,
               goffset                bytes_read,
               goffset                total_len,
               gpointer               user_data)
{
  if (progress_func != NULL)
    progress_func (bytes_read, total_len, user_data);
}

static void
download_chunk_func (GByteArray *chunk,
                     goffset     chunk_len,
                     goffset     bytes_read,
                     gpointer    chunk_func_user_data)
{
  EosDownloadFileClosure *clos = chunk_func_user_data;
  send_progress (clos->progress_func,
                 bytes_read, clos->total_len,
                 clos->user_data);
}

static void
soup_log_printer (SoupLogger *logger,
                  SoupLoggerLogLevel level,
                  char direction,
                  const char *data,
                  gpointer user_data)
{
  eos_app_log_error_message ("%s", data);
}

void
eos_net_utils_add_soup_logger (SoupSession *session)
{
  SoupLogger *logger = soup_logger_new (SOUP_LOGGER_LOG_HEADERS, -1);
  soup_session_add_feature (session, (SoupSessionFeature *) logger);
  soup_logger_set_printer (logger, soup_log_printer, NULL, NULL);
}

static gboolean
is_response_partial_content (SoupRequest *request)
{
  g_autoptr(SoupMessage) message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));
  if (message == NULL)
    return FALSE;

  eos_app_log_debug_message ("Status code: %d",  message->status_code);
  if (message->status_code != SOUP_STATUS_PARTIAL_CONTENT)
    {
      eos_app_log_error_message ("Server does not support our resume request!");
      return FALSE;
    }

  eos_app_log_debug_message ("Server supports resuming. Continuing download.");

  return TRUE;
}

static gboolean
download_from_uri (SoupSession            *session,
                   const char             *source_uri,
                   const char             *target_file,
                   GFileProgressCallback   progress_func,
                   gpointer                user_data,
                   gboolean               *reset_error_counter,
                   GCancellable           *cancellable,
                   GError                **error)
{
  /* We assume that we won't get any data from the endpoint */
  if (reset_error_counter != NULL)
    *reset_error_counter = FALSE;

  g_autoptr(SoupRequest) request = prepare_soup_request (session, source_uri, NULL, error);
  if (request == NULL)
    return FALSE;

  gboolean is_resumed = FALSE;
  goffset start_offset = 0;
  gboolean needs_download;

  eos_app_log_debug_message ("Resume allowed. "
                             "Figuring out what range to request.");
  is_resumed = prepare_soup_resume_request (request, target_file,
                                            &needs_download,
                                            &start_offset,
                                            cancellable);
  if (!needs_download)
    return TRUE;

  /* For app bundles artifacts we are guaranteed that the download directory
   * exists and has been successfully created by eos_get_bundle_download_dir().
   * Here we also return the resuming status since the server could reject our
   * request.
   */
  g_autoptr(GInputStream) in_stream = set_up_download_from_request (request, target_file,
                                                                    cancellable,
                                                                    error);
  if (in_stream == NULL)
    return FALSE;

  /* Check that the server supports our resume request */
  if (is_resumed)
    is_resumed &= is_response_partial_content (request);

  g_autoptr(GOutputStream) out_stream = prepare_out_stream (target_file, is_resumed,
                                                            cancellable,
                                                            error);
  if (out_stream == NULL)
    return FALSE;

  goffset total = start_offset + soup_request_get_content_length (request);

  /* ensure we emit a progress notification at the beginning */
  send_progress (progress_func, start_offset, total, user_data);

  EosDownloadFileClosure *clos = g_slice_new0 (EosDownloadFileClosure);
  clos->progress_func = progress_func;
  clos->user_data = user_data;
  clos->total_len = total;

  goffset bytes_read = 0;
  gboolean retval = download_file_chunks (in_stream, out_stream, start_offset,
                                          &bytes_read, download_chunk_func,
                                          clos, cancellable, error);

  g_slice_free (EosDownloadFileClosure, clos);

  /* Since we got some data, we can assume that network is back online */
  if (bytes_read > 0 && reset_error_counter != NULL)
    *reset_error_counter = TRUE;

  /* Emit a progress notification for the whole file if we successfully
   * downloaded it.
   */
  if (retval)
    send_progress (progress_func, total, total, user_data);

  return retval;
}

gboolean
eos_net_utils_download_file_with_retry (SoupSession            *session,
                                        const char             *source_uri,
                                        const char             *target_file,
                                        GFileProgressCallback   progress_func,
                                        gpointer                user_data,
                                        GCancellable           *cancellable,
                                        GError                **error_out)
{
  gboolean download_success = FALSE;
  gboolean reset_error_counter = FALSE;

  GError *error = NULL;

  gint64 retry_time_limit = MAX_DOWNLOAD_RETRY_PERIOD * G_USEC_PER_SEC;
  gint64 error_retry_cutoff = 0;

  /* Keep trying to download unless we finish successfully or we reach
   * the retry timeout
   */
  while (TRUE)
    {
      download_success = download_from_uri (session, source_uri, target_file,
                                            progress_func,
                                            user_data,
                                            &reset_error_counter,
                                            cancellable,
                                            &error);

      /* We're done if we get the file */
      if (download_success)
        break;

      /* If we're out of disk space, don't bother retrying */
      if (g_error_matches (error, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_DISK_FULL))
        {
          g_propagate_error (error_out, error);
          break;
        }

      /* If we got canceled, also bail */
      if (g_cancellable_is_cancelled (cancellable))
        {
          g_set_error_literal (error_out, G_IO_ERROR,
                               G_IO_ERROR_CANCELLED,
                               "Download cancelled");

          eos_app_log_error_message ("Download cancelled. Breaking out of retry loop.");
          break;
        }

      eos_app_log_error_message ("Error downloading. Checking if retries are needed");

      if (reset_error_counter)
        {
          eos_app_log_info_message ("Some data retrieved during download failure. "
                                    "Resetting retry timeouts.");
          error_retry_cutoff = 0;
        }

      /* If this is our first retry, record the start time */
      if (error_retry_cutoff == 0)
        error_retry_cutoff = g_get_monotonic_time () + retry_time_limit;

      /* If we reached our limit of retry time, exit */
      if (g_get_monotonic_time () >= error_retry_cutoff)
        {
          eos_app_log_error_message ("Retry limit reached. Exiting with failure");

          g_propagate_error (error_out, error);

          break;
        }

      /* Ignore the error if we need to run again */
      g_clear_error (&error);

      eos_app_log_error_message ("Retrying to download the file after a short break");

      /* Sleep for n seconds and try again */
      g_usleep (DOWNLOAD_RETRY_PERIOD * G_USEC_PER_SEC);

      eos_app_log_error_message ("Continuing download loop...");
    }

  return download_success;
}

gboolean
eos_net_utils_download_file (SoupSession     *session,
                             const char      *content_type,
                             const char      *source_uri,
                             const char      *target_file,
                             char           **buffer,
                             gboolean         use_cache,
                             gboolean        *cache_hit,
                             GCancellable    *cancellable,
                             GError         **error)
{
  eos_app_log_debug_message ("Downloading file from %s to %s. Cache: %s",
                             source_uri,
                             target_file,
                             use_cache ? "true" : "false");

  if (use_cache && check_cached_file (target_file, buffer))
    {
      if (cache_hit)
        *cache_hit = TRUE;

      return TRUE;
    }

  g_autoptr(SoupRequest) request = prepare_soup_request (session, source_uri, content_type, error);
  if (request == NULL)
    return FALSE;

  /* For non-bundle artifacts files we cannot rely on the target directory
   * to exist, so we always try and create it. If the directory already
   * exists, this is a no-op.
   */
  if (!eos_mkdir_for_artifact (target_file, error))
    return FALSE;

  g_autoptr(GInputStream) in_stream =
    set_up_download_from_request (request, target_file, cancellable, error);
  if (in_stream == NULL)
    return FALSE;

  g_autoptr(GOutputStream) out_stream =
    prepare_out_stream (target_file,
                        FALSE, /* No resuming for these right now */
                        cancellable,
                        error);
  if (out_stream == NULL)
    return FALSE;

  GByteArray *all_content = g_byte_array_new ();
  goffset bytes_read = 0;

  if (!download_file_chunks (in_stream, out_stream, 0, &bytes_read,
                             download_file_chunk_func, all_content,
                             cancellable, error))
    {
      g_byte_array_unref (all_content);
      return FALSE;
    }

  /* NUL-terminate the content and steal it */
  all_content->data[bytes_read] = 0;

  if (buffer)
    *buffer = (char *) g_byte_array_free (all_content, FALSE);
  else
    g_byte_array_unref (all_content);

  if (cache_hit)
    *cache_hit = FALSE;

  return TRUE;
}
