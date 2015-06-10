/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include <glib.h>
#include <glib/gstdio.h>
#include <glib/gi18n-lib.h>

#include <libsoup/soup.h>

#include "eos-app-log.h"
#include "eos-app-utils.h"
#include "eos-net-utils.h"

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

void
eos_net_utils_progress_closure_free (gpointer _data)
{
  EosProgressClosure *data = _data;

  g_clear_object (&data->model);
  g_object_unref (data->info);

  g_slice_free (EosProgressClosure, data);
}

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
  GFile *file = g_file_new_for_path (target_file);
  GFile *parent = g_file_get_parent (file);

  if (!eos_check_available_space (parent, total, cancellable, &internal_error))
    {
      eos_app_log_error_message ("Not enough space on FS - canceling download");

      g_propagate_error (error, internal_error);
      g_clear_object (&in_stream);
      goto out;
    }

  /* we don't use GFile API because the error handling is weird,
   * and we also know that the target is a local file, so there
   * is no point in going through the abstraction
   */
  g_unlink (target_file);

 out:
  g_object_unref (parent);
  g_object_unref (file);

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

  if (buffer == NULL)
    {
      eos_app_log_error_message ("Trying to read a file into an empty pointer!");
      return FALSE;
    }

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
          eos_app_log_error_message ("Downloading file failed during piecewise transfer");
          g_propagate_error (error, internal_error);
          goto out;
        }

      pos += res;

      if (chunk_func != NULL)
        chunk_func (content, res, pos, chunk_func_user_data);
    }

  if (g_cancellable_is_cancelled (cancellable))
    {
      char *error_message;

      eos_app_log_info_message ("Download cancelled");

      error_message = g_strdup (_("Download cancelled"));
      g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                           EOS_NET_UTILS_ERROR_CANCELLED,
                           error_message);
      g_free (error_message);

      goto out;
    }

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

#undef GET_DATA_BLOCK_SIZE

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
      char *error_message;

      eos_app_log_error_message ("Soap URI is NULL - canceling download");

      error_message = g_strdup (_("Soap URI is NULL - canceling download"));
      g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                           EOS_NET_UTILS_ERROR_INVALID_URL,
                           error_message);
      g_free (error_message);

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
                    GCancellable  *cancellable,
                    GError       **error)
{
  GError *internal_error = NULL;
  GFileOutputStream *out_stream = NULL;
  GFile *file = g_file_new_for_path (target_file);

  out_stream = g_file_create (file, G_FILE_CREATE_NONE, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      char *error_message;

      eos_app_log_error_message ("Create file failed - canceling download");

      error_message = g_strdup_printf (_("Create file failed - canceling download (%s)"),
                                         internal_error->message);

      g_set_error_literal (error, EOS_NET_UTILS_ERROR,
                           EOS_NET_UTILS_ERROR_FAILED,
                           error_message);

      g_error_free (internal_error);
      g_free (error_message);
    }

  g_object_unref (file);

  return G_OUTPUT_STREAM (out_stream);
}

static void
download_chunk_func (GByteArray *chunk,
                     gsize       chunk_len,
                     gsize       bytes_read,
                     gpointer    chunk_func_user_data)
{
  EosDownloadAppFileClosure *clos = chunk_func_user_data;

  if (clos->progress_func != NULL)
    clos->progress_func (bytes_read, clos->total_len,
                         clos->progress_func_user_data);
}

static gboolean
download_from_uri (SoupSession          *session,
                   EosAppInfo           *info,
                   const char           *source_uri,
                   const char           *target_file,
                   EosProgressReportFunc progress_func,
                   gpointer              progress_func_user_data,
                   gboolean             *reset_error_counter,
                   GCancellable         *cancellable,
                   GError              **error)
{
  gboolean retval = FALSE;

  /* We assume that we won't get any data from the endpoint */
  *reset_error_counter = FALSE;

  gsize bytes_read = 0;
  GInputStream *in_stream = NULL;
  GOutputStream *out_stream = NULL;
  SoupRequest *request = prepare_soup_request (session, source_uri, NULL, error);
  if (request == NULL)
    goto out;

  /* For app bundles artifacts we are guaranteed that the download directory
   * exists and has been successfully created by eos_get_bundle_download_dir().
   */
  in_stream = set_up_download_from_request (request, target_file, cancellable,
                                            error);
  if (in_stream == NULL)
    goto out;

  out_stream = prepare_out_stream (target_file, cancellable, error);
  if (out_stream == NULL)
    goto out;

  goffset total = soup_request_get_content_length (request);

  /* ensure we emit a progress notification at the beginning */
  if (progress_func != NULL)
    progress_func (0, total, progress_func_user_data);

  EosDownloadAppFileClosure *clos = g_slice_new0 (EosDownloadAppFileClosure);
  clos->progress_func = progress_func;
  clos->progress_func_user_data = progress_func_user_data;
  clos->info = info;
  clos->total_len = total;

  retval = download_file_chunks (in_stream, out_stream, &bytes_read,
                                 download_chunk_func,
                                 clos, cancellable, error);

  g_slice_free (EosDownloadAppFileClosure, clos);

  /* Since we got some data, we can assume that network is back online */
  if (bytes_read > 0)
    *reset_error_counter = TRUE;

  /* emit a progress notification for the whole file, in any case */
  if (progress_func != NULL)
    progress_func (total, total, progress_func_user_data);

out:
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);

  return retval;
}

/**
 * eos_net_utils_download_file_with_retry:
 * @progress_func: (closure) (scope async): Callback function to
 *                 invoke for every progress event
 *
 * Returns:
 */
gboolean
eos_net_utils_download_file_with_retry (SoupSession          *session,
                                        const char           *source_uri,
                                        const char           *target_file,
                                        EosProgressReportFunc progress_func,
                                        gpointer              progress_func_user_data,
                                        GCancellable         *cancellable,
                                        GError              **error_out)
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
        download_success = download_from_uri (session, NULL, source_uri,
                                              target_file,
                                              progress_func,
                                              progress_func_user_data,
                                              &reset_error_counter,
                                              cancellable,
                                              &error);

        /* We're done if we get the file */
        if (download_success)
            break;

        /* If we got canceled, also bail */
        if (g_error_matches (error, EOS_NET_UTILS_ERROR,
                             EOS_NET_UTILS_ERROR_CANCELLED))
          {
            eos_app_log_error_message ("Download cancelled. Breaking out of retry loop.");
            g_propagate_error (error_out, error);
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
eos_net_utils_download_file_from_uri (SoupSession     *session,
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
  if (!eos_set_up_target_dir (target_file, error))
    goto out;

  in_stream = set_up_download_from_request (request, target_file, cancellable,
                                            error);
  if (in_stream == NULL)
    goto out;

  out_stream = prepare_out_stream (target_file, cancellable, error);
  if (out_stream == NULL)
    goto out;

  if (!download_file_chunks (in_stream, out_stream, &bytes_read,
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
