/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include <glib.h>
#include <glib/gstdio.h>
#include <libsoup/soup.h>

#include "eos-app-log.h"
#include "eos-app-utils.h"
#include "eos-net-utils.h"

void
eos_net_utils_progress_closure_free (gpointer _data)
{
  EosProgressClosure *data = _data;

  g_clear_object (&data->model);
  eos_app_info_unref (data->info);

  g_slice_free (EosProgressClosure, data);
}

/**
 * eos_net_utils_set_up_download_from_request:
 * @request:
 * @target_file:
 * @cancellable:
 * @error:
 *
 * Returns: (transfer none):
 */
GInputStream *
eos_net_utils_set_up_download_from_request (SoupRequest   *request,
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
