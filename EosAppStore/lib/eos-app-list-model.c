/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include "eos-app-log.h"
#include "eos-app-list-model.h"
#include "eos-app-manager-service.h"
#include "eos-app-manager-transaction.h"
#include "eos-app-utils.h"

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

/* Amount of seconds that we should keep retrying to download the file after
 * first interruption
 */
#define MAX_DOWNLOAD_RETRY_PERIOD 20

/* Amount of seconds that we should wait before retrying a failed download */
#define DOWNLOAD_RETRY_PERIOD 4

/* Amount of seconds before a downloaded file is considered stale */
#define DOWNLOADED_FILE_STALE_THRESHOLD 3600

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

static gboolean
download_file_from_uri (SoupSession     *session,
                        const char      *content_type,
                        const char      *source_uri,
                        const char      *target_file,
                        char           **buffer,
                        gboolean         use_cache,
                        GCancellable    *cancellable,
                        GError         **error);

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
  if (!download_file_from_uri (self->soup_session, "application/json", url,
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
      gboolean updates_download_success;

      eos_app_log_info_message ("Downloading list of available apps from: %s", url);
      updates_download_success = download_file_from_uri (self->soup_session,
                                                         "application/json",
                                                         url,
                                                         target,
                                                         &data,
                                                         FALSE, /* Don't use a cache if we have it */
                                                         cancellable,
                                                         &error);

      g_free (url);

      if (!updates_download_success)
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

static gboolean
reload_model (EosAppListModel *self,
              GCancellable *cancellable,
              GError **error)
{
  gboolean retval = FALSE;

  eos_app_load_gio_apps (self->apps);

  if (!eos_app_load_installed_apps (self->apps, cancellable, error))
    eos_app_log_error_message ("Unable to load installed apps");

  if (!load_available_apps (self, cancellable, error))
    eos_app_log_error_message ("Unable to load available apps");

  if (!load_shell_apps (self, cancellable))
    {
      eos_app_log_error_message ("Unable to load shell apps");
      goto out;
    }

  if (!load_content_apps (self, cancellable))
    {
      eos_app_log_error_message ("Unable to load content apps");
      goto out;
    }

  retval = TRUE;

out:
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
      if (internal_error == NULL || internal_error->domain != EOS_APP_LIST_MODEL_ERROR)
        {
          if (internal_error != NULL)
            {
              eos_app_log_error_message ("%s", internal_error->message);
              g_error_free (internal_error);
            }

          g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                               EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                               _("We were unable to update the list of applications"));
        }
      else
        g_propagate_error (error, internal_error);
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

  g_object_unref (&self->proxy);

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
progress_closure_free (gpointer _data)
{
  ProgressClosure *data = _data;

  g_clear_object (&data->model);
  g_clear_object (&data->info);

  g_slice_free (ProgressClosure, data);
}

static gboolean
emit_download_progress (gpointer _data)
{
  ProgressClosure *data = _data;

  g_signal_emit (data->model, eos_app_list_model_signals[DOWNLOAD_PROGRESS], 0,
                 eos_app_info_get_content_id (data->info),
                 data->current,
                 data->total);

  return G_SOURCE_REMOVE;
}

static void
queue_download_progress (EosAppInfo *info,
                         goffset     current,
                         goffset     total,
                         gpointer    user_data)
{
  EosAppListModel *self = user_data;
  ProgressClosure *clos = g_slice_new (ProgressClosure);

  clos->model = g_object_ref (self);
  clos->info = g_object_ref (info);
  clos->current = current;
  clos->total = total;

  /* we need to invoke this into the main context */
  g_main_context_invoke_full (NULL, G_PRIORITY_DEFAULT,
                              emit_download_progress,
                              clos,
                              progress_closure_free);
}

static gboolean
check_available_space (GFile         *path,
                       goffset        min_size,
                       GCancellable  *cancellable,
                       GError       **error)
{
  GFileInfo *info;
  gboolean retval = TRUE;

  if (path == NULL)
    eos_app_log_error_message ("File doesn't exist");

  eos_app_log_info_message ("Trying to get filesystem info from %s",
                            g_file_get_path(path));

  info = g_file_query_filesystem_info (path, G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                       cancellable,
                                       error);
  if (info == NULL)
    {
      eos_app_log_error_message ("Can't get filesystem info to calculate"
                                 "the available space");
      return FALSE;
    }

  guint64 free_space = g_file_info_get_attribute_uint64 (info, G_FILE_ATTRIBUTE_FILESYSTEM_FREE);

  /* we try to be conservative, and reserve twice the requested size, like
   * eos-app-manager does.
   */
  guint64 req_space = min_size * 2;

  eos_app_log_info_message ("Space left on FS: %lld", (long long) req_space);

  if (free_space < req_space)
    {
      eos_app_log_error_message ("Not enough space on device for downloading app");

      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_DISK_FULL,
                   _("Not enough space on device for downloading app"));
      retval = FALSE;
    }

  g_object_unref (info);

  return retval;
}

static SoupRequest *
prepare_soup_request (SoupSession  *session,
                      const char   *source_uri,
                      const char   *content_type,
                      EosAppInfo   *info,
                      GError      **error)
{
  GError *internal_error = NULL;
  SoupURI *uri = soup_uri_new (source_uri);

  if (uri == NULL)
    {
      char *error_message;

      eos_app_log_error_message ("Soap URI is NULL - canceling download");

      if (info != NULL)
        error_message = g_strdup_printf (_("No available bundle for '%s'"),
                                         eos_app_info_get_application_id (info));
      else
        error_message = g_strdup (_("No available data on the server"));

      g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
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
            msg = _("The certificate of the app store is expired");
          else if ((cert_flags & G_TLS_CERTIFICATE_REVOKED) != 0)
            msg = _("The certificate of the app store has been revoked");
          else if ((cert_flags & G_TLS_CERTIFICATE_BAD_IDENTITY) != 0)
            msg = _("The certificate of the app store has a bad identity");
          else if ((cert_flags & G_TLS_CERTIFICATE_UNKNOWN_CA) != 0)
            msg = _("The certificate of the app store is from an unknown authority");
          else
            msg = _("The certificate of the app store is bad or invalid");

          g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                               EOS_APP_LIST_MODEL_ERROR_BAD_CERTIFICATE,
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

static gboolean
set_up_target_dir (const char *target_file,
                   GError    **error)
{
  GFile *file = g_file_new_for_path (target_file);
  GFile *parent = g_file_get_parent (file);
  gboolean res = TRUE;

  char *parent_path = g_file_get_path (parent);
  if (g_mkdir_with_parents (parent_path, 0755) == -1)
    {
      int saved_errno = errno;

      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_FAILED,
                   "Unable to create directory: %s",
                   g_strerror (saved_errno));
      res = FALSE;
    }

  g_free (parent_path);

  g_object_unref (parent);
  g_object_unref (file);

  return res;
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

  if (!check_available_space (parent, total, cancellable, &internal_error))
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

static GOutputStream *
prepare_out_stream (const char    *target_file,
                    EosAppInfo    *info,
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

      if (info != NULL)
        error_message = g_strdup_printf (_("Unable to create the file for downloading '%s': %s"),
                                         eos_app_info_get_application_id (info),
                                         internal_error->message);
      else
        error_message = g_strdup_printf (_("Unable to update the list of available applications: %s"),
                                         internal_error->message);

      g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_FAILED,
                           error_message);

      g_error_free (internal_error);
      g_free (error_message);
    }

  g_object_unref (file);

  return G_OUTPUT_STREAM (out_stream);
}

typedef void (* ChunkFunc) (GByteArray *chunk,
                            gsize       chunk_len,
                            gsize       bytes_read,
                            gpointer    chunk_func_user_data);

static gboolean
download_file_chunks (GInputStream   *in_stream,
                      GOutputStream  *out_stream,
                      EosAppInfo     *info,
                      gsize          *bytes_read,
                      ChunkFunc       chunk_func,
                      gpointer        chunk_func_user_data,
                      GCancellable   *cancellable,
                      GError        **error)
{
#define GET_DATA_BLOCK_SIZE     64 * 1024

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

      eos_app_log_info_message ("Canceled download");

      if (info != NULL)
        error_message = g_strdup_printf (_("Download of app '%s' cancelled by the user."),
                                         eos_app_info_get_application_id (info));
      else
        error_message = g_strdup (_("Refresh of available apps cancelled by the user."));

      g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_CANCELLED,
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

static gboolean
download_file_from_uri (SoupSession     *session,
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
  SoupRequest *request = prepare_soup_request (session, source_uri,
                                               content_type, NULL,
                                               error);
  if (request == NULL)
    goto out;

  /* For non-bundle artifacts files we cannot rely on the target directory
   * to exist, so we always try and create it. If the directory already
   * exists, this is a no-op.
   */ 
  if (!set_up_target_dir (target_file, error))
    goto out;

  in_stream = set_up_download_from_request (request, target_file,
                                            cancellable, error);
  if (in_stream == NULL)
    goto out;

  out_stream = prepare_out_stream (target_file, NULL,
                                   cancellable, error);
  if (out_stream == NULL)
    goto out;

  if (!download_file_chunks (in_stream, out_stream,
                             NULL, &bytes_read,
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

typedef struct {
  ProgressReportFunc  progress_func;
  gpointer            progress_func_user_data;
  EosAppInfo         *info;
  gsize               total_len;
} DownloadAppFileClosure;

static void
download_app_file_chunk_func (GByteArray *chunk,
                              gsize       chunk_len,
                              gsize       bytes_read,
                              gpointer    chunk_func_user_data)
{
  DownloadAppFileClosure *clos = chunk_func_user_data;

  if (clos->progress_func != NULL)
    clos->progress_func (clos->info,
                         bytes_read, clos->total_len,
                         clos->progress_func_user_data);
}

static gboolean
download_app_file_from_uri (SoupSession     *session,
                            EosAppInfo      *info,
                            const char      *source_uri,
                            const char      *target_file,
                            ProgressReportFunc progress_func,
                            gpointer         progress_func_user_data,
                            gboolean        *reset_error_counter,
                            GCancellable    *cancellable,
                            GError         **error)
{
  gboolean retval = FALSE;

  /* We assume that we won't get any data from the endpoint */
  *reset_error_counter = FALSE;

  gsize bytes_read = 0;
  GInputStream *in_stream = NULL;
  GOutputStream *out_stream = NULL;
  SoupRequest *request = prepare_soup_request (session, source_uri,
                                               NULL, info,
                                               error);
  if (request == NULL)
    goto out;

  /* For app bundles artifacts we are guaranteed that the download directory
   * exists and has been successfully created by eos_get_bundle_download_dir().
   */
  in_stream = set_up_download_from_request (request, target_file,
                                            cancellable, error);
  if (in_stream == NULL)
    goto out;

  out_stream = prepare_out_stream (target_file, info,
                                   cancellable, error);
  if (out_stream == NULL)
    goto out;

  goffset total = soup_request_get_content_length (request);

  /* ensure we emit a progress notification at the beginning */
  if (progress_func != NULL)
    progress_func (info, 0, total, progress_func_user_data);

  DownloadAppFileClosure *clos = g_slice_new0 (DownloadAppFileClosure);
  clos->progress_func = progress_func;
  clos->progress_func_user_data = progress_func_user_data;
  clos->info = info;
  clos->total_len = total;

  retval = download_file_chunks (in_stream, out_stream,
                                 info, &bytes_read,
                                 download_app_file_chunk_func, clos,
                                 cancellable, error);

  g_slice_free (DownloadAppFileClosure, clos);

  /* Since we got some data, we can assume that network is back online */
  if (bytes_read > 0)
    *reset_error_counter = TRUE;

  /* emit a progress notification for the whole file, in any case */
  if (progress_func != NULL)
    progress_func (info, total, total, progress_func_user_data);

out:
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);

  return retval;
}

static gboolean
download_app_file_from_uri_with_retry (SoupSession     *session,
                                       EosAppInfo      *info,
                                       const char      *source_uri,
                                       const char      *target_file,
                                       ProgressReportFunc progress_func,
                                       gpointer         progress_func_user_data,
                                       GCancellable    *cancellable,
                                       GError         **error_out)
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
        download_success = download_app_file_from_uri (session, info, source_uri,
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
        if (g_error_matches (error, EOS_APP_LIST_MODEL_ERROR,
                             EOS_APP_LIST_MODEL_ERROR_CANCELLED))
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
                   EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
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
                   EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
                   _("No signature available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *signature_name = g_strconcat (app_id, ".asc", NULL);
  char *signature_path = g_build_filename (eos_get_bundle_download_dir (), signature_name, NULL);
  g_free (signature_name);

  if (!download_app_file_from_uri_with_retry (self->soup_session, info,
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

  if (!download_app_file_from_uri_with_retry (self->soup_session, info,
                                              bundle_uri, bundle_path,
                                              queue_download_progress, self,
                                              cancellable, &error))
    {
      eos_app_log_error_message ("Download of bundle failed");

      g_propagate_error (error_out, error);
    }

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
                                                              bundle_path,
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
