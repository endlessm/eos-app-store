/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include "eos-downloader.h"

#include <glib/gstdio.h>
#include <glib/gi18n-lib.h>

#include "eos-app-enums.h"
#include "eos-app-log.h"
#include "eos-app-utils.h"
#include "eos-net-utils-private.h"

char *
eos_app_info_download_signature (EosAppInfo *info,
                                 SoupSession *soup_session,
                                 const char *download_dir,
                                 gboolean use_delta,
                                 GCancellable *cancellable,
                                 GError **error_out)
{
  GError *error = NULL;
  const char *signature_uri = NULL;
  const char *app_id = eos_app_info_get_application_id (info);

  if (use_delta)
    signature_uri = eos_app_info_get_delta_signature_uri (info);
  else
    signature_uri = eos_app_info_get_signature_uri (info);

  if (signature_uri == NULL || *signature_uri == '\0')
    {
      g_set_error (error_out, EOS_APP_STORE_ERROR,
                   EOS_APP_STORE_ERROR_SIGNATURE_MISSING,
                   _("No signature available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *signature_name = g_strconcat (app_id, ".asc", NULL);
  char *signature_path = g_build_filename (download_dir, signature_name, NULL);
  g_free (signature_name);

  if (!eos_net_utils_download_file_with_retry (soup_session,
                                               signature_uri, signature_path,
                                               NULL, NULL,
                                               cancellable, &error))
    {
      g_propagate_error (error_out, error);
    }

  return signature_path;
}

/**
 * eos_app_info_download_bundle:
 * @info:
 * @soup_session:
 * @download_dir:
 * @use_delta:
 * @cancellable:
 * @progress_callback: (scope call):
 * @progress_user_data:
 * @error_out: (out):
 *
 * Returns: (transfer full):
 */
char *
eos_app_info_download_bundle (EosAppInfo *info,
                              SoupSession *soup_session,
                              const char *download_dir,
                              gboolean use_delta,
                              GCancellable *cancellable,
                              GFileProgressCallback progress_callback,
                              gpointer progress_user_data,
                              GError **error_out)
{
  GError *error = NULL;
  const char *bundle_uri = NULL;
  const char *app_id = eos_app_info_get_application_id (info);

  if (use_delta)
    bundle_uri = eos_app_info_get_delta_bundle_uri (info);
  else
    bundle_uri = eos_app_info_get_bundle_uri (info);

  eos_app_log_info_message ("Downloading - app id: %s (%s), bundle URI: %s",
                            app_id,
                            eos_app_info_get_available_version (info),
                            bundle_uri);

  if (bundle_uri == NULL || *bundle_uri == '\0')
    {
      eos_app_log_error_message ("Bundle URI is bad. Canceling");

      g_set_error (error_out, EOS_APP_STORE_ERROR,
                   EOS_APP_STORE_ERROR_FAILED,
                   _("Application bundle '%s' could not be downloaded"),
                   app_id);
      return NULL;
    }

  char *extension = use_delta ? ".xdelta": ".bundle";
  char *bundle_name = g_strconcat (app_id, extension, NULL);

  char *bundle_path = g_build_filename (download_dir, bundle_name, NULL);
  g_free (bundle_name);

  eos_app_log_info_message ("Bundle save path is %s", bundle_path);

  if (!eos_net_utils_download_file_with_retry (soup_session, bundle_uri,
                                               bundle_path,
                                               progress_callback,
                                               progress_user_data,
                                               cancellable, &error))
    {
      eos_app_log_error_message ("Download of bundle failed: %s", error->message);

      g_propagate_error (error_out, error);
    }

  return bundle_path;
}

static gint64
get_local_updates_monotonic_id (void)
{
  char *url = eos_get_updates_meta_record_uri ();
  char *target = eos_get_updates_meta_record_file ();
  char *data = NULL;

  GError *error = NULL;

  gint64 monotonic_id = -1;

  if (!g_file_get_contents (target, &data, NULL, &error))
    {
      eos_app_log_error_message ("Unable to load updates meta record: %s: %s",
                                 target,
                                 error->message);

      goto out;
    }

  if (!eos_app_load_updates_meta_record (&monotonic_id, data, NULL, &error))
    {
      eos_app_log_error_message ("Unable to parse updates meta record: %s: %s. "
                                 "Removing file from system",
                                 target,
                                 error->message);

      /* If we have parsing issues with the file, we want it removed from the
       * system regardless of the reasons */
      g_unlink (target);

      goto out;
    }

out:
  g_free (url);
  g_free (target);
  g_free (data);

  g_clear_error (&error);

  return monotonic_id;
}

static gboolean
check_is_app_list_current (SoupSession *soup_session,
                           GCancellable *cancellable)
{
  char *url = eos_get_updates_meta_record_uri ();
  char *target = eos_get_updates_meta_record_file ();
  char *data = NULL;

  gint64 old_monotonic_id = 0;
  gint64 monotonic_id = 0;
  gboolean updates_current = FALSE;

  GError *error = NULL;

  eos_app_log_info_message ("Checking if app list update is needed");
  old_monotonic_id = get_local_updates_monotonic_id ();

  eos_app_log_info_message ("Downloading updates meta record from: %s", url);
  if (!eos_net_utils_download_file (soup_session,
                                    "application/json",
                                    url,
                                    target,
                                    &data,
                                    TRUE, /* Use cached copy if we have it */
                                    cancellable,
                                    &error))
    {
      eos_app_log_error_message ("Unable to get updates meta record: %s",
                                 error->message);
      goto out;
    }

  if (!eos_app_load_updates_meta_record (&monotonic_id, data, cancellable,
                                         &error))
    {
      eos_app_log_error_message ("Unable to parse updates meta record: %s. "
                                 "Removing cached file.", error->message);

      /* If we have parsing issues with the file, we want it removed from the
       * system regardless of the reasons */
      g_unlink (target);

      goto out;
    }

  eos_app_log_info_message ("Comparing monotonic update ID."
                            " Old: %" G_GINT64_FORMAT ","
                            " New: %" G_GINT64_FORMAT ".",
                            old_monotonic_id,
                            monotonic_id);

  /* If monotonic IDs don't match, we need to update our app list */
  if (monotonic_id == old_monotonic_id)
    updates_current = TRUE;

out:
  eos_app_log_info_message ("App list updates are %scurrent",
                            updates_current ? "" : "not ");

  /* Clean up */
  g_free (url);
  g_free (target);
  g_free (data);

  /* We eat the errors since we assume that it just means that
   * we'll re-download the updates */
  g_clear_error (&error);

  return updates_current;
}

char *
eos_refresh_available_apps (SoupSession *soup_session,
                            GCancellable *cancellable,
                            GError **error_out)
{
  eos_app_log_debug_message ("Reloading available apps");

  char *target = eos_get_updates_file ();
  char *data = NULL;
  gboolean updates_current;

  GError *error = NULL;

  updates_current = check_is_app_list_current (soup_session, cancellable);

  /* Try a manual load of the data */
  if (updates_current)
    {
      eos_app_log_info_message ("Loading cached updates.json");
      if (!g_file_get_contents (target, &data, NULL, &error))
        {
          eos_app_log_error_message ("Loading cached updates.json failed: %s. "
                                     "Need to re-download it", error->message);

          /* We clear the error because we want to force a re-download */
          g_clear_error (&error);
        }
    }

  /* If update needed or we couldn't load cached file, get it again */
  if (!data)
    {
      char *url = eos_get_all_updates_uri ();
      gboolean updates_dl_success;

      eos_app_log_info_message ("Downloading list of available apps from: %s", url);
      updates_dl_success = eos_net_utils_download_file (soup_session,
                                                        "application/json",
                                                        url,
                                                        target,
                                                        &data,
                                                        FALSE, /* Don't use a cache if we have it */
                                                        cancellable,
                                                        &error);

      g_free (url);

      if (!updates_dl_success)
        {
          eos_app_log_error_message ("Download of all updates failed: %s",
                                     error->message);

          g_free (target);
          g_propagate_error (error_out, error);

          return NULL;
        }
    }

  g_free (target);
  return data;
}
