/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include "eos-app-log.h"
#include "eos-app-list-model.h"
#include "eos-app-manager-service.h"
#include "eos-app-manager-transaction.h"
#include "eos-app-utils.h"
#include "eos-net-utils-private.h"

#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

#include <glib-object.h>
#include <glib/gstdio.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <glib/gi18n-lib.h>
#include <libsoup/soup.h>

/* The delay for the EosAppListModel::changed signal, in milliseconds */
#define CHANGED_DELAY   500

/* HACK: This will be revisited for the next release,
 * but for now we have a limited number of app language ids,
 * with no country codes, so we can iterate through them
 * looking for installed apps using other langauge ids.
 * If not available in current language, English is the
 * preferred next option, so list it first.
 */
static const char *app_lang_ids[] = { "-en", "-ar", "-es_GT", "-es", "-fr", "-pt", NULL };

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *system_bus;
  GDBusConnection *session_bus;

  GAppInfoMonitor *app_monitor;

  GHashTable *apps;

  guint applications_changed_id;
  guint changed_guard_id;

  gboolean can_install;
  gboolean can_uninstall;
  gboolean caps_loaded;

  SoupSession *soup_session;

  EosAppManager *proxy;
};

struct _EosAppListModelClass
{
  GObjectClass parent_class;
};

enum {
  CHANGED,
  DOWNLOAD_PROGRESS,

  LAST_SIGNAL
};

static guint eos_app_list_model_signals[LAST_SIGNAL] = { 0, };

typedef struct
{
  EosAppListModel *model;
  EosAppInfo *info;
} DownloadProgressCallbackData;

static void
download_progress_callback_data_free (DownloadProgressCallbackData *data)
{
  g_object_unref (data->model);
  g_object_unref (data->info);

  g_slice_free (DownloadProgressCallbackData, data);
}

G_DEFINE_TYPE (EosAppListModel, eos_app_list_model, G_TYPE_OBJECT)
G_DEFINE_QUARK (eos-app-list-model-error-quark, eos_app_list_model_error)

static EosAppManager *
get_eam_dbus_proxy (EosAppListModel *self)
{
  eos_app_log_debug_message ("Getting dbus proxy");

  /* If we already have a proxy, return it */
  if (self->proxy != NULL)
    return self->proxy;

  /* Otherwise create it */
  GError *error = NULL;

  eos_app_log_debug_message ("No dbus proxy object yet - creating it");

  self->proxy = eos_app_manager_proxy_new_for_bus_sync (G_BUS_TYPE_SYSTEM,
                                                        G_DBUS_PROXY_FLAGS_NONE,
                                                        "com.endlessm.AppManager",
                                                        "/com/endlessm/AppManager",
                                                        NULL, /* GCancellable* */
                                                        &error);
  g_dbus_proxy_set_default_timeout (G_DBUS_PROXY (self->proxy), G_MAXINT);

  if (error != NULL)
    eos_app_log_error_message ("Unable to create dbus proxy");

  return self->proxy;
}

static gboolean
emit_queued_changed (gpointer data)
{
  EosAppListModel *self = data;

  self->changed_guard_id = 0;

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);

  return G_SOURCE_REMOVE;
}

static void
eos_app_list_model_emit_changed (EosAppListModel *self)
{
  if (self->changed_guard_id == 0)
    self->changed_guard_id = g_idle_add (emit_queued_changed, self);
}

#define WEB_LINK_ID_PREFIX "eos-link-"

static gboolean
desktop_id_is_web_link (const gchar *desktop_id)
{
  return g_str_has_prefix (desktop_id, WEB_LINK_ID_PREFIX);
}

static gchar *
app_id_from_desktop_id (const gchar *desktop_id)
{
  gint len;

  len = strlen (desktop_id);

  /* We check to make sure the string is actually a .desktop file */
  /* The 8 here is the length of ".desktop" */
  g_assert_false (len <= 8);

  return g_strndup (desktop_id, len - 8);
}

static gchar **
get_language_ids (void)
{
  const gchar * const * locales;
  const gchar *locale_name;
  gchar **variants;
  GPtrArray *lang_ids;
  gint idx;

  lang_ids = g_ptr_array_new ();
  locales = g_get_language_names ();
  locale_name = locales[0];

  /* We want to return an array with all the possible variants
   * for the current locale, except those that specify an encoding,
   * since our language IDs all assume UTF-8.
   */
  variants = g_get_locale_variants (locale_name);
  for (idx = 0; variants[idx] != NULL; idx++)
    {
      /* Variants with encoding are identified with a dot */
      if (g_strrstr (variants[idx], ".") != NULL)
        continue;

      g_ptr_array_add (lang_ids, g_strdup_printf ("-%s", variants[idx]));
    }

  g_ptr_array_add (lang_ids, NULL);
  g_strfreev (variants);

  return (gchar **) g_ptr_array_free (lang_ids, FALSE);
}

static gchar *
localized_id_from_desktop_id (const gchar *desktop_id,
                              const gchar *lang_id)
{
  gchar *localized_id;
  gchar *app_id;

  app_id = app_id_from_desktop_id (desktop_id);
  localized_id = g_strdup_printf ("%s%s.desktop", app_id, lang_id);

  g_free (app_id);

  return localized_id;
}

static EosAppInfo *
get_localized_app_info (EosAppListModel *model,
                        const gchar *desktop_id,
                        gboolean language_fallback)
{
  EosAppInfo *info;
  gchar *localized_id;
  gchar **lang_ids;
  gint idx;

  lang_ids = get_language_ids ();

  for (idx = 0; lang_ids[idx] != NULL; idx++)
    {
      localized_id = localized_id_from_desktop_id (desktop_id, lang_ids[idx]);

      info = g_hash_table_lookup (model->apps, localized_id);
      g_free (localized_id);

      if (info)
        {
          g_strfreev (lang_ids);
          return info;
        }
    }

  g_strfreev (lang_ids);

  if (!language_fallback)
    return NULL;

  /* If app is not installed in the user's current language,
   * consider all other supported languages, starting with English.
   */
  for (idx = 0; app_lang_ids[idx] != NULL; idx++)
    {
      const char *suffix = app_lang_ids[idx];
      localized_id = localized_id_from_desktop_id (desktop_id, suffix);
      info = g_hash_table_lookup (model->apps, localized_id);
      g_free (localized_id);

      if (info)
        return info;
    }

  return NULL;
}

/**
 * eos_app_list_model_get_app_info:
 * @model: the app list model
 * @desktop_id : the id of the app
 *
 * Returns the #EosAppInfo for the given app.
 *
 * Returns: (transfer none): A #EosAppInfo
 */
static EosAppInfo *
eos_app_list_model_get_app_info (EosAppListModel *model,
                                 const char *desktop_id)
{
  EosAppInfo *info = g_hash_table_lookup (model->apps, desktop_id);

  if (info == NULL)
    info = get_localized_app_info (model, desktop_id, TRUE);

  return info;
}

static void
on_app_monitor_changed (GAppInfoMonitor *monitor,
                        EosAppListModel *self)
{
  eos_app_load_gio_apps (self->apps);
  eos_app_load_installed_apps (self->apps, NULL, NULL);

  eos_app_list_model_emit_changed (self);
}

static void
on_shell_applications_changed (GDBusConnection *connection,
                               const gchar     *sender_name,
                               const gchar     *object_path,
                               const gchar     *interface_name,
                               const gchar     *signal_name,
                               GVariant        *parameters,
                               gpointer         user_data)
{
  EosAppListModel *self = user_data;

  eos_app_load_shell_apps (self->apps, parameters);

  eos_app_list_model_emit_changed (self);
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
      eos_app_log_error_message ("Unable to load updates meta record: %s: %s!",
                                 target,
                                 error->message);

      goto out;
    }

  if (!eos_app_load_updates_meta_record (&monotonic_id, data, NULL, &error))
    {
      eos_app_log_error_message ("Unable to parse updates meta record: %s: %s! "
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
check_is_app_list_current (EosAppListModel *self,
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

  eos_app_log_info_message ("Downloading updates meta record from: %s", url);
  if (!eos_net_utils_download_file (self->soup_session,
                                    "application/json",
                                    url,
                                    target,
                                    &data,
                                    TRUE, /* Use cached copy if we have it */
                                    cancellable,
                                    &error))
    {
      eos_app_log_error_message ("Unable to get updates meta record!");
      goto out;
    }

  if (!eos_app_load_updates_meta_record (&monotonic_id, data, cancellable,
                                         &error))
    {
      eos_app_log_error_message ("Unable to parse updates meta record! "
                                 "Removing cached file.");

      /* If we have parsing issues with the file, we want it removed from the
       * system regardless of the reasons */
      g_unlink (target);

      goto out;
    }

  old_monotonic_id = get_local_updates_monotonic_id ();
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

  if (error)
    {
      eos_app_log_error_message ("Failed checkng if update is needed!: %s. "
                                 "Ignoring and assuming that update is needed",
                                 error->message);

      /* We eat the errors since we assume that it just means that
       * we'll re-download the updates */
      g_clear_error (&error);
    }

  return updates_current;
}

static gboolean
load_available_apps (EosAppListModel *self,
                     GCancellable *cancellable,
                     GError **error_out)
{
  eos_app_log_debug_message ("Reloading available apps");

  char *target = eos_get_updates_file ();
  char *data = NULL;
  gboolean updates_current;

  GError *error = NULL;

  updates_current = check_is_app_list_current (self, cancellable);

  /* Try a manual load of the data */
  if (updates_current)
    {
      eos_app_log_info_message ("Loading cached updates.json");
      if (!g_file_get_contents (target, &data, NULL, &error))
        {
          eos_app_log_error_message ("Loading cached updates.json failed. "
                                     "Need to re-download it");

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
      updates_dl_success = eos_net_utils_download_file (self->soup_session,
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
          eos_app_log_error_message ("Download of all updates failed!");

          g_free (target);
          g_propagate_error (error_out, error);

          return FALSE;
        }
    }

  if (!eos_app_load_available_apps (self->apps, data, cancellable, &error))
    {
      eos_app_log_error_message ("Parsing of all updates failed!");

      g_free (data);
      g_propagate_error (error_out, error);

      return FALSE;
    }

  g_free (data);
  g_free (target);

  return TRUE;
}

static gboolean
load_user_capabilities (EosAppListModel *self,
                        GCancellable *cancellable,
                        GError **error_out)
{
  GVariant *capabilities;
  GError *error = NULL;

  if (self->caps_loaded)
    return TRUE;

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      g_set_error_literal (error_out, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_FAILED,
                           _("The app store has detected a fatal error and "
                             "cannot continue with the installation. Please, "
                             "restart your system. If the problem persists, "
                             "please contact support."));
      return FALSE;
    }

  eos_app_log_info_message ("Trying to get user capabilities");

  eos_app_manager_call_get_user_capabilities_sync (proxy,
                                                   &capabilities,
                                                   cancellable,
                                                   &error);

  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to list retrieve user capabilities: %s",
                                 error->message);
      g_critical ("Unable to retrieve user capabilities: %s",
                  error->message);

      return FALSE;
    }

  g_variant_lookup (capabilities, "CanInstall", "b", &self->can_install);
  g_variant_lookup (capabilities, "CanUninstall", "b", &self->can_uninstall);
  g_variant_unref (capabilities);

  self->caps_loaded = TRUE;

  eos_app_log_debug_message ("CanInstall: %s",
                             self->can_install ? "Yes" : "No");
  eos_app_log_debug_message ("CanUninstall: %s",
                             self->can_uninstall ? "Yes" : "No");

  return TRUE;
}

static gboolean
load_shell_apps (EosAppListModel *self,
                 GCancellable *cancellable)
{
  GError *error = NULL;
  eos_app_log_debug_message ("Reloading shell launchers");

  GVariant *applications =
    g_dbus_connection_call_sync (self->session_bus,
                                 "org.gnome.Shell",
                                 "/org/gnome/Shell",
                                 "org.gnome.Shell.AppStore",
                                 "ListApplications",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 cancellable,
                                 &error);
  if (error != NULL)
    {
      g_critical ("Unable to list available applications: %s", error->message);
      g_error_free (error);
      return FALSE;
    }

  eos_app_load_shell_apps (self->apps, applications);
  g_variant_unref (applications);

  return TRUE;
}

static gboolean
load_content_apps (EosAppListModel *self,
                   GCancellable *cancellable)
{
  eos_app_log_debug_message ("Reloading content apps");

  JsonArray *array = eos_app_parse_resource_content ("apps", "content", NULL);

  if (array == NULL)
    return FALSE;

  guint i, n_elements = json_array_get_length (array);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (array, i);

      JsonObject *obj = json_node_get_object (element);
      if (!json_object_has_member (obj, "application-id"))
        continue;

      const char *app_id = json_object_get_string_member (obj, "application-id");
      char *desktop_id = g_strconcat (app_id, ".desktop", NULL);

      EosAppInfo *info = eos_app_list_model_get_app_info (self, desktop_id);
      g_free (desktop_id);

      eos_app_log_info_message ("Updating content info for %s (%s)",
                                app_id ? app_id : "null",
                                info ? eos_app_info_get_desktop_id (info) : "null");

      if (info == NULL)
        continue;

      eos_app_info_update_from_content (info, obj);
    }

  json_array_unref (array);

  return TRUE;
}

static void
set_reload_error (GError **error,
                  gboolean is_critical,
                  char *message)
{
  eos_app_log_error_message ("Reload error: %s", message);

  if (*error == NULL || is_critical)
    {
      int error_type = EOS_APP_LIST_MODEL_ERROR_APP_REFRESH_PARTIAL_FAILURE;

      if (is_critical)
        {
          g_clear_error (error);

          error_type = EOS_APP_LIST_MODEL_ERROR_APP_REFRESH_FAILURE;
        }

      g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR, error_type,
                           message);
    }
}

static gboolean
reload_model (EosAppListModel *self,
              GCancellable *cancellable,
              GError **error)
{
  /* Since each step can fail independently, we assume a success result
   * unless any of the loading steps explicitly flips the flag
   */
  gboolean retval = TRUE;

  GError *internal_error = NULL;

  eos_app_load_gio_apps (self->apps);

  if (!eos_app_load_installed_apps (self->apps, cancellable, &internal_error))
    {
      /* We eat the message */
      g_error_free (internal_error);

      set_reload_error (error, FALSE, _("Unable to load installed apps"));

      retval = FALSE;
    }

  if (!load_available_apps (self, cancellable, &internal_error))
    {
      /* We eat the message */
      g_error_free (internal_error);

      set_reload_error (error, FALSE, _("Unable to load available apps"));

      retval = FALSE;
    }

  if (!load_shell_apps (self, cancellable))
    {
      set_reload_error (error, TRUE, _("Unable to load shell apps"));

      retval = FALSE;
    }

  if (!load_content_apps (self, cancellable))
    {
      set_reload_error (error, TRUE, _("Unable to load content apps"));

      retval = FALSE;
    }

  return retval;
}

static gboolean
load_all_apps (EosAppListModel *self,
               GCancellable *cancellable,
               GError **error)
{
  GError *internal_error = NULL;
  gboolean retval = reload_model (self, cancellable, &internal_error);

  if (!retval)
    {
      eos_app_log_debug_message ("Model reload error. "
                                 "Deciding if we need to ignore the error");

      /* Sanity check */
      g_assert_nonnull (internal_error);

      if (internal_error->domain == EOS_APP_LIST_MODEL_ERROR)
        {
          eos_app_log_debug_message ("Propagating reload error to caller");

          g_propagate_error (error, internal_error);
        }
      else
        {
          /* Debug purposes only since we eat the message anyways */
          eos_app_log_error_message ("Error: %s", internal_error->message);
          g_error_free (internal_error);

          g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                               EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                               _("We were unable to update the list of applications"));
        }
    }

  return retval;
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  if (self->applications_changed_id != 0)
    {
      g_dbus_connection_signal_unsubscribe (self->session_bus,
                                            self->applications_changed_id);
      self->applications_changed_id = 0;
    }

  if (self->changed_guard_id != 0)
    {
      g_source_remove (self->changed_guard_id);
      self->changed_guard_id = 0;
    }

  g_clear_object (&self->proxy);

  g_clear_object (&self->soup_session);

  g_clear_object (&self->app_monitor);
  g_clear_object (&self->session_bus);
  g_clear_object (&self->system_bus);

  g_hash_table_unref (self->apps);

  G_OBJECT_CLASS (eos_app_list_model_parent_class)->finalize (gobject);
}

static void
eos_app_list_model_class_init (EosAppListModelClass *klass)
{
  G_OBJECT_CLASS (klass)->finalize = eos_app_list_model_finalize;

  eos_app_list_model_signals[CHANGED] =
    g_signal_new (g_intern_static_string ("changed"),
                  G_OBJECT_CLASS_TYPE (klass),
                  G_SIGNAL_RUN_LAST,
                  0,
                  NULL, NULL,
                  g_cclosure_marshal_VOID__VOID,
                  G_TYPE_NONE, 0);

  eos_app_list_model_signals[DOWNLOAD_PROGRESS] =
    g_signal_new (g_intern_static_string ("download-progress"),
                  G_OBJECT_CLASS_TYPE (klass),
                  G_SIGNAL_RUN_LAST,
                  0,
                  NULL, NULL,
                  NULL,
                  G_TYPE_NONE, 3,
                  G_TYPE_STRING,   // app-id
                  G_TYPE_UINT64,   // current progress
                  G_TYPE_UINT64);  // total size
}

static void
eos_app_list_model_init (EosAppListModel *self)
{
  self->system_bus = g_bus_get_sync (G_BUS_TYPE_SYSTEM, NULL, NULL);
  self->session_bus = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);

  self->applications_changed_id =
    g_dbus_connection_signal_subscribe (self->session_bus,
                                        "org.gnome.Shell",
                                        "org.gnome.Shell.AppStore",
                                        "ApplicationsChanged",
                                        "/org/gnome/Shell",
                                        NULL, G_DBUS_SIGNAL_FLAGS_NONE,
                                        on_shell_applications_changed,
                                        self, NULL);

  self->app_monitor = g_app_info_monitor_get ();
  g_signal_connect (self->app_monitor, "changed",
                    G_CALLBACK (on_app_monitor_changed),
                    self);

  self->apps = g_hash_table_new_full (g_str_hash, g_str_equal,
                                      g_free,
                                      (GDestroyNotify) g_object_unref);

  eos_app_log_error_message ("Creating new soup session");

  self->soup_session = soup_session_new ();

  /* Add soup logger to session if needed */
  if (eos_app_log_soup_debug_enabled())
      eos_net_utils_add_soup_logger (self->soup_session);
}

EosAppListModel *
eos_app_list_model_new (void)
{
  return g_object_new (EOS_TYPE_APP_LIST_MODEL, NULL);
}

static void
refresh_thread_func (GTask *task,
                     gpointer source_object,
                     gpointer task_data,
                     GCancellable *cancellable)
{
  EosAppListModel *model = source_object;
  GError *error = NULL;

  if (!load_user_capabilities (model, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  if (!load_all_apps (model, cancellable, &error))
    {
      eos_app_log_info_message ("Failed to load apps. "
                                "Returning error to dbus invoker");

      g_task_return_error (task, error);
      return;
    }

  g_task_return_boolean (task, TRUE);
}

void
eos_app_list_model_refresh_async (EosAppListModel *model,
                                  GCancellable *cancellable,
                                  GAsyncReadyCallback callback,
                                  gpointer user_data)
{
  GTask *task = g_task_new (model, cancellable, callback, user_data);
  g_task_run_in_thread (task, refresh_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_refresh_finish (EosAppListModel *model,
                                   GAsyncResult *result,
                                   GError **error)
{
  return g_task_propagate_boolean (G_TASK (result), error);
}

static gboolean
launch_app (EosAppListModel *self,
            EosAppInfo *info,
            guint32 timestamp,
            GCancellable *cancellable,
            GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;
  const char *desktop_id = eos_app_info_get_desktop_id (info);
  GVariant *res;

  res = g_dbus_connection_call_sync (self->session_bus,
                                     "org.gnome.Shell",
                                     "/org/gnome/Shell",
                                     "org.gnome.Shell.AppLauncher", "Launch",
                                     g_variant_new ("(su)",
                                                    desktop_id,
                                                    timestamp),
                                     G_VARIANT_TYPE ("(b)"),
                                     G_DBUS_CALL_FLAGS_NONE,
                                     -1,
                                     NULL,
                                     &error);

  if (error != NULL)
    {
      g_critical ("Unable to launch application '%s': %s",
                  desktop_id,
                  error->message);
      g_propagate_error (error_out, error);

      retval = FALSE;
    }

  if (res != NULL)
    {
      g_variant_get (res, "(b)", &retval);
      g_variant_unref (res);
    }

  return retval;
}

static gboolean
add_app_to_shell (EosAppListModel *self,
                  EosAppInfo *info,
                  GCancellable *cancellable,
                  GError **error_out)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->session_bus,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "AddApplication",
                               g_variant_new ("(s)", eos_app_info_get_desktop_id (info)),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               -1,
                               NULL,
                               &error);

  if (error != NULL)
    {
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return TRUE;
}

typedef void (* ProgressReportFunc) (EosAppInfo *info,
                                     goffset current,
                                     goffset total,
                                     gpointer user_data);

typedef struct {
  EosAppListModel *model;
  EosAppInfo *info;
  goffset current;
  goffset total;
} ProgressClosure;

static void
emit_download_progress (goffset current, goffset total, gpointer _data)
{
  DownloadProgressCallbackData *user_data = _data;

  /* If we're downloading a signature, we won't have the info object */
  if (user_data->info)
      g_signal_emit (user_data->model,
                     eos_app_list_model_signals[DOWNLOAD_PROGRESS], 0,
                     eos_app_info_get_content_id (user_data->info),
                     current,
                     total);
}

static char *
create_sha256sum (EosAppListModel *self,
                  EosAppInfo *info,
                  gboolean use_delta,
                  const char *bundle_path,
                  GCancellable *cancellable,
                  GError **error_out)
{
  GError *error = NULL;
  const char *bundle_hash = NULL;
  const char *app_id = eos_app_info_get_application_id (info);

  if (use_delta)
    bundle_hash = eos_app_info_get_delta_bundle_hash (info);
  else
    bundle_hash = eos_app_info_get_bundle_hash (info);

  if (bundle_hash == NULL || *bundle_hash == '\0')
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_CHECKSUM_MISSING,
                   _("No verification available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *sha256_name = g_strconcat (app_id, ".sha256", NULL);
  char *sha256_path = g_build_filename (eos_get_bundle_download_dir (), sha256_name, NULL);
  g_free (sha256_name);

  gchar *contents = g_strconcat (bundle_hash, "\t", bundle_path, "\n", NULL);
  if (!g_file_set_contents (sha256_path, contents, -1, &error))
    g_propagate_error (error_out, error);

  g_free (contents);

  return sha256_path;
}

static char *
download_signature (EosAppListModel *self,
                    EosAppInfo *info,
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
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_SIGNATURE_MISSING,
                   _("No signature available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *signature_name = g_strconcat (app_id, ".asc", NULL);
  char *signature_path = g_build_filename (eos_get_bundle_download_dir (), signature_name, NULL);
  g_free (signature_name);

  if (!eos_net_utils_download_file_with_retry (self->soup_session,
                                               signature_uri, signature_path,
                                               NULL, NULL,
                                               cancellable, &error))
    {
      g_propagate_error (error_out, error);
    }

  return signature_path;
}

static char *
download_bundle (EosAppListModel *self,
                 EosAppInfo *info,
                 gboolean use_delta,
                 GCancellable *cancellable,
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

      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_FAILED,
                   _("Application bundle '%s' could not be downloaded"),
                   app_id);
      return NULL;
    }

  char *bundle_name = g_strconcat (app_id, ".bundle", NULL);
  char *bundle_path = g_build_filename (eos_get_bundle_download_dir (), bundle_name, NULL);
  g_free (bundle_name);

  eos_app_log_info_message ("Bundle save path is %s", bundle_path);

  DownloadProgressCallbackData *data = g_slice_new (DownloadProgressCallbackData);
  data->model = g_object_ref (self);
  data->info = g_object_ref (info);

  if (!eos_net_utils_download_file_with_retry (self->soup_session, bundle_uri,
                                               bundle_path,
                                               emit_download_progress, data,
                                               cancellable, &error))
    {
      eos_app_log_error_message ("Download of bundle failed");

      g_propagate_error (error_out, error);
    }

  download_progress_callback_data_free (data);

  return bundle_path;
}

static gboolean
get_bundle_artifacts (EosAppListModel *self,
                      EosAppInfo *info,
                      char *transaction_path,
                      gboolean use_delta,
                      GCancellable *cancellable,
                      GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;

  char *bundle_path = NULL;
  char *signature_path = NULL;
  char *sha256_path = NULL;

  eos_app_log_info_message ("Accessing dbus transaction");

  EosAppManagerTransaction *transaction =
    eos_app_manager_transaction_proxy_new_sync (self->system_bus,
                                                G_DBUS_PROXY_FLAGS_NONE,
                                                "com.endlessm.AppManager",
                                                transaction_path,
                                                cancellable,
                                                &error);
  g_dbus_proxy_set_default_timeout (G_DBUS_PROXY (transaction), G_MAXINT);

  if (error != NULL)
    {
      eos_app_log_error_message ("Getting dbus transaction failed");
      goto out;
    }

  eos_app_log_info_message ("Downloading bundle (use_delta: %s)",
                            use_delta ? "true" : "false");
  bundle_path = download_bundle (self, info, use_delta, cancellable, &error);
  if (error != NULL)
    {
      eos_app_log_info_message ("Download of bundle failed");
      goto out;
    }

  eos_app_log_info_message ("Downloading signature");
  signature_path = download_signature (self, info, use_delta, cancellable,
                                       &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Signature download failed");
      goto out;
    }

  eos_app_log_info_message ("Persisting hash");
  sha256_path = create_sha256sum (self, info, use_delta, bundle_path,
                                  cancellable,
                                  &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Hash download failed");
      goto out;
    }

  eos_app_log_info_message ("Completing transaction with eam");

  eos_app_manager_transaction_call_complete_transaction_sync (transaction,
                                                              eos_get_bundle_download_dir (),
                                                              &retval,
                                                              cancellable,
                                                              &error);

out:
  if (error != NULL)
    {
      eos_app_log_error_message ("Completion of transaction %s failed",
                                 transaction_path);

      /* cancel the transaction on error */
      if (transaction != NULL)
        eos_app_manager_transaction_call_cancel_transaction_sync (transaction, NULL, NULL);

      /* Bubble the error up */
      g_propagate_error (error_out, error);

      retval = FALSE;
    }

  /* delete the downloaded bundle and signature */
  if (bundle_path)
    g_unlink (bundle_path);
  if (signature_path)
    g_unlink (signature_path);
  if (sha256_path)
    g_unlink (sha256_path);

  /* We're done with the transaction now that we've called CompleteTransaction() */
  g_clear_object (&transaction);
  g_free (bundle_path);
  g_free (signature_path);
  g_free (sha256_path);

  return retval;
}

static void
set_app_installation_error (const char *desktop_id,
                            const char *internal_message,
                            const char *external_message,
                            GError **error_out)
{
  /* Show errors in journal */
  eos_app_log_error_message ("Error: %s", internal_message);
  eos_app_log_error_message ("Error (user-visible): %s", external_message);

  /* Show errors in session log */
  g_warning ("Error: %s", internal_message);
  g_warning ("Error (user-visible): %s", external_message);

  /* Set user-visible error */
  if (external_message == NULL)
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_INSTALL_FAILED,
                   _("Application '%s' could not be installed"),
                   desktop_id);
    }
  else
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_INSTALL_FAILED,
                   _("Application '%s' could not be installed. %s"),
                   desktop_id,
                   external_message);
    }
}

static void
set_app_uninstall_error (const char *desktop_id,
                         const char *internal_message,
                         const char *external_message,
                         GError **error_out)
{
  /* Show errors in journal */
  eos_app_log_error_message ("Error: %s", internal_message);
  eos_app_log_error_message ("Error (user-visible): %s", external_message);

  /* Show errors in session log */
  g_warning ("Error: %s", internal_message);
  g_warning ("Error (user-visible): %s", external_message);

  /* Set user-visible error */
  if (external_message == NULL)
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                   _("Application '%s' could not be removed"),
                   desktop_id);
    }
  else
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                   _("Application '%s' could not be removed. %s"),
                   desktop_id,
                   external_message);
    }
}

static gboolean
install_latest_app_version (EosAppListModel *self,
                            EosAppInfo *info,
                            const gboolean is_upgrade,
                            const gboolean allow_deltas,
                            GCancellable *cancellable,
                            GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;

  const char *app_id = eos_app_info_get_application_id (info);
  const char *desktop_id = eos_app_info_get_desktop_id (info);
  const char *internal_message = NULL;
  const char *external_message = NULL;

  if (!self->can_install)
    {
      external_message = _("You must be an administrator to install applications");
      goto out;
    }

  /* We do a double check here, to catch the case where the app manager
   * proxy was successfully created, but the app bundles directory was
   * removed afterwards
   */
  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL ||
      !g_file_test (eos_get_bundles_dir (), G_FILE_TEST_EXISTS))
    {
      external_message = _("The app store has detected a fatal error and "
                           "cannot continue. Please, "
                           "restart your system. If the problem persists, "
                           "please contact support.");
      goto out;
    }

  char *transaction_path = NULL;

  /* We use different DBus targets but everything else is same */
  if (is_upgrade)
    {
      eos_app_log_info_message ("Calling update (deltas: %s) dbus method with app_id: %s",
                                allow_deltas ? "enabled" : "disabled",
                                app_id);
      eos_app_manager_call_update_sync (proxy, app_id, allow_deltas,
                                        &transaction_path,
                                        NULL,
                                        &error);
    }
  else
    {
      eos_app_log_info_message ("Calling install dbus method with app_id: %s", app_id);
      eos_app_manager_call_install_sync (proxy, app_id,
                                         &transaction_path,
                                         NULL,
                                         &error);
    }

  if (error != NULL)
    {
      /* the app manager may send us specific errors */
      if (g_dbus_error_is_remote_error (error))
        {
          char *code = g_dbus_error_get_remote_error (error);

          if (g_strcmp0 (code, "com.endlessm.AppManager.Error.NotAuthorized") == 0)
            external_message = _("You must be an administrator to install applications");

          g_free (code);
        }

      internal_message = error->message;
      goto out;
    }

  if (transaction_path == NULL || *transaction_path == '\0')
    {
      internal_message = "Transaction path is empty - canceling";
      goto out;
    }

  eos_app_log_info_message ("Got transaction path: %s", transaction_path);

  gboolean use_delta = allow_deltas && is_upgrade;

  retval = get_bundle_artifacts (self, info, transaction_path, use_delta,
                                 cancellable, &error);

  if (error != NULL)
    {
      /* propagate only the errors we generate as they are... */
      if (error->domain == EOS_APP_LIST_MODEL_ERROR)
        external_message = error->message;

      internal_message = error->message;
      goto out;
    }

  if (is_upgrade)
    {
      eos_app_info_installed_changed (info);
      eos_app_list_model_emit_changed (self);
    }

 out:
  if (!retval && !internal_message)
    internal_message = "Install transaction failed";

  if (!retval)
    set_app_installation_error (desktop_id,
                                internal_message,
                                external_message,
                                error_out);

  g_clear_error (&error);
  g_free (transaction_path);

  return retval;
}

static gboolean
add_app_from_manager (EosAppListModel *self,
                      EosAppInfo *info,
                      GCancellable *cancellable,
                      GError **error_out)
{
  return install_latest_app_version (self,
                                     info,
                                     FALSE, /* Is update? */
                                     FALSE, /* Allow deltas (not applicable) */
                                     cancellable,
                                     error_out);
}

static gboolean
update_app_from_manager (EosAppListModel *self,
                         EosAppInfo *info,
                         GCancellable *cancellable,
                         GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;
  gboolean use_deltas = eos_use_delta_updates ();
  const char *desktop_id = eos_app_info_get_desktop_id (info);

  eos_app_log_info_message ("Attempting to update '%s' (using deltas: %s)",
                            desktop_id, use_deltas ? "true" : "false");

  retval = install_latest_app_version (self,
                                       info,
                                       TRUE, /* Is update? */
                                       use_deltas,
                                       cancellable,
                                       &error);

  /* Incremental update failed */
  if (!retval)
    {
      eos_app_log_info_message ("Update of '%s' (using deltas: %s) failed: %s",
                                desktop_id, use_deltas ? "true" : "false",
                                error->message);
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return TRUE;
}

static gboolean
remove_app_from_shell (EosAppListModel *self,
                       EosAppInfo *info,
                       GCancellable *cancellable,
                       GError **error_out)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->session_bus,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "RemoveApplication",
                               g_variant_new ("(s)", eos_app_info_get_desktop_id (info)),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               -1,
                               cancellable,
                               &error);

  if (error != NULL)
    {
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return TRUE;
}

static gboolean
remove_app_from_manager (EosAppListModel *self,
                         EosAppInfo *info,
                         GCancellable *cancellable,
                         GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;

  const char *app_id = eos_app_info_get_application_id (info);
  const char *desktop_id = eos_app_info_get_desktop_id (info);
  const char *internal_message = NULL;
  const char *external_message = NULL;

  if (!self->can_uninstall)
    {
      external_message = _("You must be an administrator to remove applications");
      goto out;
    }

  /* We do a double check here, to catch the case where the app manager
   * proxy was successfully created, but the app bundles directory was
   * removed afterwards
   */
  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL ||
      !g_file_test (eos_get_bundles_dir (), G_FILE_TEST_EXISTS))
    {
      external_message = _("The app store has detected a fatal error and "
                           "cannot continue. Please, "
                           "restart your system. If the problem persists, "
                           "please contact support.");
      goto out;
    }

  eos_app_log_info_message ("Trying to uninstall %s", app_id);
  eos_app_manager_call_uninstall_sync (proxy, app_id, &retval, NULL, &error);

  if (error != NULL)
    {
      /* the app manager may send us specific errors */
      if (g_dbus_error_is_remote_error (error))
        {
          char *code = g_dbus_error_get_remote_error (error);

          if (g_strcmp0 (code, "com.endlessm.AppManager.Error.NotAuthorized") == 0)
            external_message = _("You must be an administrator to remove applications");

          g_free (code);
        }

      internal_message = error->message;
      goto out;
    }

 out:
  if (!retval && !internal_message)
    internal_message = "Uninstall transaction failed";

  if (retval)
    eos_app_log_info_message ("Uninstall transaction succeeded");
  else
    set_app_uninstall_error (desktop_id,
                             internal_message,
                             external_message,
                             error_out);
  g_clear_error (&error);

  return retval;
}

/**
 * eos_app_list_model_get_apps_for_category:
 * @model:
 * @category:
 *
 * Returns: (transfer container) (element-type EosAppInfo):
 */
GList *
eos_app_list_model_get_apps_for_category (EosAppListModel *model,
                                          EosAppCategory category)
{
  GList *apps = NULL;
  JsonArray *array = eos_app_parse_resource_content ("apps", "content", NULL);

  if (array == NULL)
    return NULL;

  guint i, n_elements = json_array_get_length (array);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (array, i);

      JsonObject *obj = json_node_get_object (element);
      const char *category_id = json_object_get_string_member (obj, "category");
      EosAppCategory obj_category = eos_app_category_from_id (category_id);

      if (category == obj_category ||
          category == EOS_APP_CATEGORY_INSTALLED ||
          category == EOS_APP_CATEGORY_ALL)
        {
          const char *app_id = json_object_get_string_member (obj, "application-id");
          char *desktop_id = g_strconcat (app_id, ".desktop", NULL);

          EosAppInfo *info = g_hash_table_lookup (model->apps, desktop_id);

          if (info == NULL)
            info = get_localized_app_info (model, desktop_id, FALSE);

          g_free (desktop_id);

          if (info != NULL)
            apps = g_list_prepend (apps, info);
        }
    }

  json_array_unref (array);

  return g_list_reverse (apps);
}

gboolean
eos_app_list_model_get_app_has_launcher (EosAppListModel *model,
                                         const char *desktop_id)
{
  EosAppInfo *info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return FALSE;

  return eos_app_info_get_has_launcher (info);
}

static void
add_app_thread_func (GTask *task,
                     gpointer source_object,
                     gpointer task_data,
                     GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  EosAppInfo *info = task_data;

  if (!eos_app_info_is_installed (info))
    {
      if (!desktop_id_is_web_link (eos_app_info_get_desktop_id (info)) &&
          !add_app_from_manager (model, info, cancellable, &error))
        {
          g_task_return_error (task, error);
          return;
        }
     }

  if (!add_app_to_shell (model, info, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  g_task_return_boolean (task, TRUE);
}

void
eos_app_list_model_install_app_async (EosAppListModel *model,
                                      const gchar *desktop_id,
                                      GCancellable *cancellable,
                                      GAsyncReadyCallback callback,
                                      gpointer user_data)
{
  GTask *task;
  EosAppInfo *info;

  task = g_task_new (model, cancellable, callback, user_data);
  info = eos_app_list_model_get_app_info (model, desktop_id);

  if (info == NULL)
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_FAILED,
                               _("App %s not installable"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (eos_app_info_is_installed (info) &&
      eos_app_info_get_has_launcher (info))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_INSTALLED,
                               _("App %s already installed"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, add_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_install_app_finish (EosAppListModel *model,
                                       GAsyncResult *result,
                                       GError **error)
{
  return g_task_propagate_boolean (G_TASK (result), error);
}

static void
update_app_thread_func (GTask *task,
                        gpointer source_object,
                        gpointer task_data,
                        GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  EosAppInfo *info = task_data;

  if (!update_app_from_manager (model, info, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  g_task_return_boolean (task, TRUE);
}

void
eos_app_list_model_update_app_async (EosAppListModel *model,
                                     const gchar *desktop_id,
                                     GCancellable *cancellable,
                                     GAsyncReadyCallback callback,
                                     gpointer user_data)
{
  GTask *task;
  EosAppInfo *info;

  task = g_task_new (model, cancellable, callback, user_data);
  info = eos_app_list_model_get_app_info (model, desktop_id);

  if (info == NULL)
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_FAILED,
                               _("App %s not installable"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (!eos_app_info_is_updatable (info))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                               _("App %s is up to date"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, update_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_update_app_finish (EosAppListModel *model,
                                      GAsyncResult *result,
                                      GError **error)
{
  return g_task_propagate_boolean (G_TASK (result), error);
}

static void
remove_app_thread_func (GTask *task,
                        gpointer source_object,
                        gpointer task_data,
                        GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  EosAppInfo *info = task_data;

  if (!remove_app_from_manager (model, info, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  eos_app_log_debug_message ("Removing app from shell");

  if (!remove_app_from_shell (model, info, cancellable, &error))
    {
      eos_app_log_error_message ("Unable to remove app '%s' from shell!",
                                 eos_app_info_get_application_id (info));
      g_task_return_error (task, error);
      return;
    }

  eos_app_log_debug_message ("Removed app '%s' from shell",
                             eos_app_info_get_application_id (info));

  g_task_return_boolean (task, TRUE);
}

void
eos_app_list_model_uninstall_app_async (EosAppListModel *model,
                                        const gchar *desktop_id,
                                        GCancellable *cancellable,
                                        GAsyncReadyCallback callback,
                                        gpointer user_data)
{
  GTask *task;
  EosAppInfo *info;

  eos_app_log_info_message ("Attempting to uninstall: %s", desktop_id);

  task = g_task_new (model, cancellable, callback, user_data);
  info = eos_app_list_model_get_app_info (model, desktop_id);

  if (info == NULL || !eos_app_info_is_installed (info))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NOT_INSTALLED,
                               _("App %s is not installed"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, remove_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_uninstall_app_finish (EosAppListModel *model,
                                         GAsyncResult *result,
                                         GError **error)
{
  return g_task_propagate_boolean (G_TASK (result), error);
}

gboolean
eos_app_list_model_launch_app (EosAppListModel *model,
                               const char *desktop_id,
                               guint32 timestamp,
                               GError **error)
{
  EosAppInfo *info = eos_app_list_model_get_app_info (model, desktop_id);

  if ((info == NULL) || !eos_app_info_is_installed (info))
    {
      g_set_error (error,
                   eos_app_list_model_error_quark (),
                   EOS_APP_LIST_MODEL_ERROR_NOT_INSTALLED,
                   _("App %s is not installed"),
                   desktop_id);
      return FALSE;
    }

  return launch_app (model, info, timestamp, NULL, error);
}

/**
 * eos_app_list_model_create_from_filename:
 * @model:
 * @filename:
 *
 * Returns: (transfer none):
 */
EosAppInfo *
eos_app_list_model_create_from_filename (EosAppListModel *model,
                                         const char *filename)
{
  EosAppInfo *info;
  GDesktopAppInfo *desktop_info;
  const char *desktop_id;
  char *app_id;

  desktop_info = g_desktop_app_info_new_from_filename (filename);
  if (desktop_info == NULL)
    return NULL;

  desktop_id = g_app_info_get_id (G_APP_INFO (desktop_info));
  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    {
      app_id = app_id_from_desktop_id (desktop_id);
      info = eos_app_info_new (app_id);
      g_free (app_id);

      g_hash_table_replace (model->apps, g_strdup (desktop_id), info);
    }

  eos_app_info_update_from_gio (info, desktop_info);
  g_object_unref (desktop_info);

  return info;
}
