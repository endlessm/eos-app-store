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

typedef void (* EosChunkFunc)          (GByteArray *chunk,
                                        gsize       chunk_len,
                                        gsize       bytes_read,
                                        gpointer    chunk_func_user_data);

typedef struct {
  gsize                  total_len;
  GFileProgressCallback  progress_func;
  gpointer               user_data;
} EosDownloadFileClosure;

typedef struct {
  goffset               current;
  goffset               total;
  GFileProgressCallback progress_func;
  GDestroyNotify        free_func;
  gpointer              user_data;
} EosProgressClosure;

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
      eos_app_log_error_message ("Soup request sending had an internal error");

      g_propagate_error (error, internal_error);
      return NULL;
    }

  goffset total = soup_request_get_content_length (request);

  if (!eos_check_available_space (target_file, total, cancellable, &internal_error))
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
  g_assert_nonnull (buffer);

  struct stat buf;
  if (stat (target_file, &buf) != 0)
    return FALSE;

  GNetworkMonitor *monitor = g_network_monitor_get_default ();
  gboolean network_available = g_network_monitor_get_network_available (monitor);

  GError *internal_error = NULL;

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

  if (!g_file_get_contents (target_file, buffer, NULL, &internal_error))
    {
      /* Fall through, and re-download the file */
      eos_app_log_error_message ("Could not read cached file '%s': %s",
                                 target_file,
                                 internal_error->message);
      g_clear_error (&internal_error);
      return FALSE;
    }

  return TRUE;
}

static void
download_file_chunk_func (GByteArray *chunk,
                          gsize       chunk_len,
                          gsize       bytes_read,
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
                      gsize           offset,
                      gsize          *bytes_read,
                      EosChunkFunc    chunk_func,
                      gpointer        chunk_func_user_data,
                      GCancellable   *cancellable,
                      GError        **error)
{
  gboolean retval = FALSE;
  GError *internal_error = NULL;
  gssize res = 0;
  gsize pos = 0;
  GByteArray *content = g_byte_array_sized_new (GET_DATA_BLOCK_SIZE);

  eos_app_log_info_message ("Downloading file chunks start");

  /* we don't use splice() because the data is coming from a network
   * request, so it won't have a file descriptor we can use splice()
   * on.
   */
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
  g_clear_pointer (&content, g_byte_array_unref);

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
  GError *internal_error = NULL;
  SoupURI *uri = soup_uri_new (source_uri);

  if (uri == NULL)
    {
      eos_app_log_error_message ("Soup URI is NULL - canceling download");

      g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                           EOS_NET_UTILS_ERROR_INVALID_URL,
                           "No URI provided - cancelling download");

      return NULL;
    }

  SoupRequest *request = soup_session_request_uri (session, uri, &internal_error);

  soup_uri_free (uri);

  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Soup request had an internal error: %s",
                                 internal_error->message);

      if (g_type_is_a (G_OBJECT_TYPE (request), SOUP_TYPE_REQUEST_HTTP) &&
          g_error_matches (internal_error, G_TLS_ERROR, G_TLS_ERROR_BAD_CERTIFICATE))
        {
          SoupMessage *message;

          message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));

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
      SoupMessage *message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));
      if (message != NULL)
        {
          soup_message_headers_append (message->request_headers, "Accept", content_type);
          g_object_unref (message);
        }
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
  GFile *file = g_file_new_for_path (target_file);

  /* If we are not allowed resuming, the resume file is not there, or
   * the server returned a strange status code, we need to start from
   * scratch to ensure that we don't leave junk around
   */
  if (!is_resumed)
    {
      /* we don't use GFile API because the error handling is weird,
       * and we also know that the target is a local file, so there
       * is no point in going through the abstraction
       */
      g_unlink (target_file);
    }

  out_stream = g_file_append_to (file, G_FILE_CREATE_NONE, cancellable,
                                 &internal_error);
  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Opening output file failed - canceling download");

      g_set_error (error, EOS_NET_UTILS_ERROR,
                   EOS_NET_UTILS_ERROR_FAILED,
                   _("Could not save bundle file - "
                     "canceling download (%s)"),
                   internal_error->message);

      g_error_free (internal_error);
    }

  g_object_unref (file);

  return G_OUTPUT_STREAM (out_stream);
}

static gboolean
prepare_soup_resume_request (const SoupRequest *request,
                             const char        *source_uri,
                             const char        *target_file,
                             gsize             *resume_offset,
                             GCancellable      *cancellable)
{
  GFile *file = NULL;
  GFileInfo *info = NULL;
  GError *error = NULL;

  gboolean using_resume = FALSE;

  eos_app_log_debug_message ("Getting local file length");

  file = g_file_new_for_path (target_file);
  info = g_file_query_info (file, G_FILE_ATTRIBUTE_STANDARD_SIZE,
                            G_FILE_QUERY_INFO_NOFOLLOW_SYMLINKS,
                            cancellable,
                            &error);
  if (error)
    {
      eos_app_log_info_message ("Cannot resume - unable to get "
                                "local file's size (%s: %s).",
                                target_file,
                                error->message);
      goto out;
    }

  guint64 size = g_file_info_get_attribute_uint64 (info,
                                                   G_FILE_ATTRIBUTE_STANDARD_SIZE);

  /* No file or nothing downloaded - just get the whole file */
  if (size == 0)
    goto out;

  eos_app_log_info_message ("Resuming %s from offset %" G_GUINT64_FORMAT,
                            target_file,
                            size);

  SoupMessage *message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));

  if (message == NULL)
    {
      eos_app_log_error_message ("Could not apply header to SOUP message");
      goto out;
    }

  /* -1 for end range is to make sure that libsoup doesn't include the
   * end number or the server will reject the message range and return
   * a 206. See github.com/endlessm/eos-shell/issues/4596#issuecomment-111574913
   * for more info
   */
  soup_message_headers_set_range (message->request_headers, size, -1);
  g_object_unref (message);

  *resume_offset = size;

  /* If we get to here, we're set on using the partial download */
  using_resume = TRUE;

out:
  g_clear_error (&error);

  g_clear_object (&file);
  g_clear_object (&info);

  return using_resume;
}

static void
progress_closure_free (gpointer _data)
{
  EosProgressClosure *clos = _data;

  /* Free data from caller if we are on the last invocation */
  if (clos->free_func)
    clos->free_func (clos->user_data);

  g_slice_free (EosProgressClosure, _data);
}

/* Needs to be invoked within main context */
static gboolean
send_progress_to_caller (gpointer _data)
{
  EosProgressClosure *clos = _data;

  g_assert_nonnull (clos->progress_func);

  clos->progress_func (clos->current, clos->total, clos->user_data);

  return G_SOURCE_REMOVE;
}

static void
send_progress_to_main_context (GFileProgressCallback  progress_func,
                               goffset                bytes_read,
                               goffset                total_len,
                               gpointer               user_data,
                               GDestroyNotify         free_func)
{
  EosProgressClosure *clos = g_slice_new (EosProgressClosure);
  clos->current = bytes_read;
  clos->total = total_len;
  clos->user_data = user_data;
  clos->progress_func = progress_func;
  clos->free_func = free_func;

  /* we need to pass this to the main context */
  g_main_context_invoke_full (NULL, G_PRIORITY_DEFAULT,
                              send_progress_to_caller,
                              clos,
                              progress_closure_free);
}

static void
download_chunk_func (GByteArray *chunk,
                     gsize       chunk_len,
                     gsize       bytes_read,
                     gpointer    chunk_func_user_data)
{
  EosDownloadFileClosure *clos = chunk_func_user_data;

  if (clos->progress_func != NULL)
    /* we need to invoke this into the main context */
    send_progress_to_main_context (clos->progress_func, bytes_read, clos->total_len,
                                   clos->user_data,
                                   NULL);
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
  gboolean is_partial_content = FALSE;
  SoupMessage *message = soup_request_http_get_message (SOUP_REQUEST_HTTP (request));
  if (message != NULL)
    {
      eos_app_log_debug_message ("Status code: %d",  message->status_code);

      if (message->status_code == SOUP_STATUS_PARTIAL_CONTENT)
        {
          eos_app_log_debug_message ("Server supports resuming. "
                                     "Continuing download");
          is_partial_content = TRUE;
        }
      else
        {
          eos_app_log_error_message ("Server does not support our resume request!");
        }

      g_object_unref (message);
    }

  return is_partial_content;
}

static gboolean
download_from_uri (SoupSession            *session,
                   const char             *source_uri,
                   const char             *target_file,
                   const gboolean          allow_resume,
                   GFileProgressCallback   progress_func,
                   GDestroyNotify          free_func,
                   gpointer                user_data,
                   gboolean               *reset_error_counter,
                   GCancellable           *cancellable,
                   GError                **error)
{
  gboolean retval = FALSE;

  /* We assume that we won't get any data from the endpoint */
  *reset_error_counter = FALSE;

  GInputStream *in_stream = NULL;
  GOutputStream *out_stream = NULL;

  gsize bytes_read = 0;
  gsize start_offset = 0;
  gboolean is_resumed = FALSE;

  SoupRequest *request = prepare_soup_request (session, source_uri, NULL, error);
  if (request == NULL)
    goto out;

  if (allow_resume)
    {
      eos_app_log_debug_message ("Resume allowed. "
                                 "Figuring out what range to request.");
      is_resumed = prepare_soup_resume_request (request, source_uri, target_file,
                                                &start_offset,
                                                cancellable);
    }

  /* For app bundles artifacts we are guaranteed that the download directory
   * exists and has been successfully created by eos_get_bundle_download_dir().
   * Here we also return the resuming status since the server could reject our
   * request.
   */
  in_stream = set_up_download_from_request (request, target_file, cancellable,
                                            error);
  if (in_stream == NULL)
    goto out;

  /* Check that the server supports our resume request */
  if (is_resumed)
    is_resumed &= is_response_partial_content (request);

  out_stream = prepare_out_stream (target_file, is_resumed, cancellable, error);
  if (out_stream == NULL)
    goto out;

  goffset total = start_offset + soup_request_get_content_length (request);

  /* ensure we emit a progress notification at the beginning */
  /* we need to invoke this into the main context */
  if (progress_func != NULL)
    send_progress_to_main_context (progress_func, start_offset, total,
                                   user_data, NULL);

  EosDownloadFileClosure *clos = g_slice_new0 (EosDownloadFileClosure);
  clos->progress_func = progress_func;
  clos->user_data = user_data;
  clos->total_len = total;

  retval = download_file_chunks (in_stream, out_stream, start_offset,
                                 &bytes_read, download_chunk_func,
                                 clos, cancellable, error);

  g_slice_free (EosDownloadFileClosure, clos);

  /* Since we got some data, we can assume that network is back online */
  if (bytes_read > 0)
      *reset_error_counter = TRUE;

  /* Emit a progress notification for the whole file if we successfully
   * downloaded it otherwise we want to free the caller's user data later
   * (if failures) due to retries in the caller.
   */
  if (retval) {
      if (progress_func != NULL)
          send_progress_to_main_context (progress_func, total, total, user_data,
                                         free_func);
      else if (free_func != NULL)
          free_func (user_data);
    }

out:
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);

  return retval;
}

gboolean
eos_net_utils_download_file_with_retry (SoupSession            *session,
                                        const char             *source_uri,
                                        const char             *target_file,
                                        GFileProgressCallback   progress_func,
                                        GDestroyNotify          free_func,
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
                                              TRUE, /* Allow resume */
                                              progress_func,
                                              free_func,
                                              user_data,
                                              &reset_error_counter,
                                              cancellable,
                                              &error);

        /* We're done if we get the file */
        if (download_success)
            break;

        /* If we got canceled, also bail */
        if (g_cancellable_is_cancelled (cancellable))
          {
             g_set_error_literal (error_out, EOS_NET_UTILS_ERROR,
                                  EOS_NET_UTILS_ERROR_CANCELLED,
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

    /* On failures we didn't free the caller's data yet */
    if (!download_success && free_func)
      free_func (user_data);

    return download_success;
}

gboolean
eos_net_utils_download_file (SoupSession     *session,
                             const char      *content_type,
                             const char      *source_uri,
                             const char      *target_file,
                             char           **buffer,
                             gboolean         use_cache,
                             GCancellable    *cancellable,
                             GError         **error)
{
  eos_app_log_debug_message ("Downloading file from %s to %s. Cache: %s",
                             source_uri,
                             target_file,
                             use_cache ? "true" : "false");

  if (use_cache && check_cached_file (target_file, buffer))
    return TRUE;

  gboolean retval = FALSE;
  gsize bytes_read = 0;
  GInputStream *in_stream = NULL;
  GOutputStream *out_stream = NULL;
  GByteArray *all_content = g_byte_array_new ();
  SoupRequest *request = prepare_soup_request (session, source_uri, content_type, error);
  if (request == NULL)
    goto out;

  /* For non-bundle artifacts files we cannot rely on the target directory
   * to exist, so we always try and create it. If the directory already
   * exists, this is a no-op.
   */
  if (!eos_mkdir_for_artifact (target_file, error))
    goto out;

  in_stream = set_up_download_from_request (request, target_file, cancellable,
                                            error);
  if (in_stream == NULL)
    goto out;

  out_stream = prepare_out_stream (target_file,
                                   FALSE, /* No resuming for these right now */
                                   cancellable,
                                   error);
  if (out_stream == NULL)
    goto out;

  if (!download_file_chunks (in_stream, out_stream, 0, &bytes_read,
                             download_file_chunk_func, all_content,
                             cancellable, error))
    goto out;

  /* NUL-terminate the content */
  all_content->data[bytes_read] = 0;
  *buffer = (char *) g_byte_array_free (all_content, FALSE);

  retval = TRUE;

out:
  g_byte_array_unref (all_content);
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);

  return retval;
}
