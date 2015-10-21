/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include "eos-app-enums.h"
#include "eos-app-log.h"
#include "eos-app-list-model.h"
#include "eos-app-manager-service.h"
#include "eos-app-manager-transaction.h"
#include "eos-app-utils.h"
#include "eos-downloader.h"
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

#define DOWNLOAD_RATE_LIMIT_MS 150
#define FALLBACK_LANG   "-en"

#define FATAL_ERROR_MESSAGE \
  _("The app center has detected an error and cannot continue. Please " \
    "restart your system. If the problem persists, please contact support.")

/* gdbus-codegen does not generate autoptr macros for us */
G_DEFINE_AUTOPTR_CLEANUP_FUNC (EosAppManagerTransaction, g_object_unref)

/* HACK: This will be revisited for the next release,
 * but for now we have a limited number of app language ids,
 * with no country codes, so we can iterate through them
 * looking for installed apps using other langauge ids.
 * If not available in current language, English is the
 * preferred next option, so list it first.
 */
static const char *app_lang_ids[] = { FALLBACK_LANG, "-ar", "-es_GT", "-es", "-fr", "-pt", NULL };

/* This list of languages will not try to include the fallback
 * applications
 */
static const char *app_lang_fallback_blacklist[] = { "-es_GT", "-es", "-pt", NULL };

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *system_bus;
  GDBusConnection *session_bus;

  GAppInfoMonitor *app_monitor;

  GHashTable *apps;

  guint applications_changed_id;
  guint refresh_guard_id;

  gboolean can_install;
  gboolean can_uninstall;
  gboolean caps_loaded;

  SoupSession *soup_session;
  JsonArray *content_apps;
};

struct _EosAppListModelClass
{
  GObjectClass parent_class;
};

enum {
  CHANGED,

  LAST_SIGNAL
};

static guint eos_app_list_model_signals[LAST_SIGNAL] = { 0, };

typedef struct
{
  EosAppListModel *model;
  EosAppInfo *info;

  gint64 last_notification;
} DownloadProgressCallbackData;

static void
download_progress_callback_data_free (gpointer _data)

{
  DownloadProgressCallbackData *data = _data;

  g_object_unref (data->model);
  g_object_unref (data->info);

  g_slice_free (DownloadProgressCallbackData, data);
}


static void eos_app_list_model_async_initable_iface_init (GAsyncInitableIface *iface);
G_DEFINE_TYPE_WITH_CODE (EosAppListModel, eos_app_list_model, G_TYPE_OBJECT,
                         G_IMPLEMENT_INTERFACE (G_TYPE_ASYNC_INITABLE,
                                                eos_app_list_model_async_initable_iface_init))

static void
eos_app_list_model_emit_changed (EosAppListModel *self)
{
  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
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

static gboolean
lang_fallback_allowed (void)
{
  gboolean fallback_allowed = TRUE;
  gchar **lang_ids = get_language_ids ();

  /* Iterate over our languages and see if our current one shouldn't
   * fall back to English. We cannot only check first language as we
   * might have specific and non-specific versions in the list ("pt"
   * and "pt_BR") so we need to iterate over all to match correctly.
   */
  for (int idx = 0; lang_ids[idx] != NULL; idx++)
      for (int bl_idx = 0; app_lang_fallback_blacklist[bl_idx] != NULL; bl_idx++)
          if (g_strcmp0 (lang_ids[idx], app_lang_fallback_blacklist[bl_idx]) == 0)
            {
              fallback_allowed = FALSE;
              goto out;
            }

out:
  g_strfreev (lang_ids);

  return fallback_allowed;
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
                        const gchar *desktop_id)
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

  /* If we allow a fallback for this language set,
   * check if we have an app with that suffix
   */
  if (lang_fallback_allowed ())
    {
      localized_id = localized_id_from_desktop_id (desktop_id, FALLBACK_LANG);
      info = g_hash_table_lookup (model->apps, localized_id);
      g_free (localized_id);

      if (info)
        return info;
    }

  /* Check any on-system apps that might not match our allowed locales */
  for (idx = 0; app_lang_ids[idx] != NULL; idx++)
    {
      const char *suffix = app_lang_ids[idx];
      localized_id = localized_id_from_desktop_id (desktop_id, suffix);
      info = g_hash_table_lookup (model->apps, localized_id);
      g_free (localized_id);

      /* Only return things that are installed */
      if (info && eos_app_info_is_installed (info))
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
    info = get_localized_app_info (model, desktop_id);

  return info;
}

static void
eos_app_list_model_refresh_installed (EosAppListModel *self)
{
  eos_app_load_gio_apps (self->apps);
  eos_app_load_installed_apps (self->apps, NULL);

  eos_app_list_model_emit_changed (self);
}

static gboolean
emit_queued_refresh_installed (gpointer data)
{
  EosAppListModel *self = data;

  self->refresh_guard_id = 0;
  eos_app_list_model_refresh_installed (self);

  return G_SOURCE_REMOVE;
}

static void
eos_app_list_model_queue_refresh_installed (EosAppListModel *self)
{
  if (self->refresh_guard_id == 0)
    self->refresh_guard_id = g_idle_add (emit_queued_refresh_installed, self);
}

static void
on_app_monitor_changed (GAppInfoMonitor *monitor,
                        EosAppListModel *self)
{
  eos_app_list_model_refresh_installed (self);
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

static gboolean
load_user_capabilities (EosAppListModel *self,
                        GCancellable *cancellable,
                        GError **error_out)
{
  GVariant *capabilities;
  GError *error = NULL;

  if (self->caps_loaded)
    return TRUE;

  EosAppManager *proxy = eos_get_eam_dbus_proxy ();
  if (proxy == NULL)
    {
      g_set_error_literal (error_out, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_FAILED,
                           FATAL_ERROR_MESSAGE);
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
      g_propagate_error (error_out, error);

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

static void
load_content_apps (EosAppListModel *self)
{
  eos_app_log_debug_message ("Reloading content apps");

  guint i, n_elements = json_array_get_length (self->content_apps);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (self->content_apps, i);

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
}

static void
set_reload_error (GTask *task,
                  gboolean is_critical)
{
  int error_type = EOS_APP_STORE_ERROR_APP_REFRESH_PARTIAL_FAILURE;
  char *error_message = _("We are unable to load the complete list of "
                          "applications");

  eos_app_log_error_message ("Error during refresh");

  if (is_critical)
    {
      error_type = EOS_APP_STORE_ERROR_APP_REFRESH_FAILURE;
      error_message = _("We were unable to update the list of applications");
    }

  g_task_return_new_error (task, EOS_APP_STORE_ERROR, error_type,
                           "%s", error_message);
}

static gboolean
eos_app_list_model_init_finish (GAsyncInitable *initable,
                                GAsyncResult *result,
                                GError **error)
{
  return g_task_propagate_boolean (G_TASK (result), error);
}

static void
init_model_thread_func (GTask *task,
                        gpointer source_object,
                        gpointer task_data,
                        GCancellable *cancellable)
{
  EosAppListModel *self = source_object;
  GError *error = NULL;

  self->content_apps = eos_app_parse_resource_content ("apps", "content", &error);
  if (error != NULL)
    {
      g_task_return_error (task, error);
      return;
    }

  eos_app_load_gio_apps (self->apps);

  if (!load_user_capabilities (self, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  if (!eos_app_load_installed_apps (self->apps, cancellable))
    {
      set_reload_error (task, FALSE);
      return;
    }

  /* This will load the (possibly stale) last cached updates.json,
   * so we ignore errors.
   */
  if (!eos_app_load_available_apps (self->apps, cancellable, &error))
    {
      /* We eat the message */
      g_error_free (error);
    }

  if (!load_shell_apps (self, cancellable))
    {
      set_reload_error (task, TRUE);
      return;
    }

  load_content_apps (self);

  g_task_return_boolean (task, TRUE);
}

static void
eos_app_list_model_init_async (GAsyncInitable *initable,
                               int io_priority,
                               GCancellable *cancellable,
                               GAsyncReadyCallback callback,
                               gpointer user_data)
{
  GTask *task = g_task_new (initable, cancellable, callback, user_data);
  g_task_run_in_thread (task, init_model_thread_func);
  g_object_unref (task);
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

  if (self->refresh_guard_id != 0)
    {
      g_source_remove (self->refresh_guard_id);
      self->refresh_guard_id = 0;
    }

  g_clear_pointer (&self->content_apps, json_array_unref);
  g_clear_object (&self->soup_session);

  g_clear_object (&self->app_monitor);
  g_clear_object (&self->session_bus);
  g_clear_object (&self->system_bus);

  g_hash_table_unref (self->apps);

  G_OBJECT_CLASS (eos_app_list_model_parent_class)->finalize (gobject);
}

static void
eos_app_list_model_async_initable_iface_init (GAsyncInitableIface *iface)
{
  iface->init_async = eos_app_list_model_init_async;
  iface->init_finish = eos_app_list_model_init_finish;
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

  eos_app_log_debug_message ("Creating new soup session");

  self->soup_session = soup_session_new ();

  /* Add soup logger to session if needed */
  if (eos_app_log_soup_debug_enabled())
      eos_net_utils_add_soup_logger (self->soup_session);
}

void
eos_app_list_model_new_async (GCancellable *cancellable,
                              GAsyncReadyCallback callback,
                              gpointer user_data)
{
  g_async_initable_new_async (EOS_TYPE_APP_LIST_MODEL, G_PRIORITY_DEFAULT,
                              cancellable, callback, user_data,
                              NULL);
}

EosAppListModel *
eos_app_list_model_new_finish (GAsyncResult *result,
                               GError **error)
{
  GAsyncInitable *initable = G_ASYNC_INITABLE (g_async_result_get_source_object (result));
  return EOS_APP_LIST_MODEL (g_async_initable_new_finish (initable, result, error));
}

static void
refresh_network_thread_func (GTask *task,
                             gpointer source_object,
                             gpointer task_data,
                             GCancellable *cancellable)
{
  EosAppListModel *self = source_object;
  GError *internal_error = NULL;
  char *data;

  data = eos_refresh_available_apps (self->soup_session,
                                     cancellable, &internal_error);
  if (internal_error != NULL)
    {
      /* We eat the message */
      g_error_free (internal_error);

      set_reload_error (task, FALSE);
      return;
    }

  g_task_return_pointer (task, data, g_free);
}

void
eos_app_list_model_refresh_network_async (EosAppListModel *model,
                                          GCancellable *cancellable,
                                          GAsyncReadyCallback callback,
                                          gpointer user_data)
{
  GTask *task = g_task_new (model, cancellable, callback, user_data);
  g_task_run_in_thread (task, refresh_network_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_refresh_network_finish (EosAppListModel *model,
                                           GAsyncResult *result,
                                           GError **error)
{
  char *data = g_task_propagate_pointer (G_TASK (result), error);
  gboolean res;

  if (data == NULL)
    return FALSE;

  res = eos_app_load_available_apps_from_data (model->apps, data, NULL, error);
  g_free (data);

  /* Now refresh content attributes */
  if (res)
    load_content_apps (model);

  return res;
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

typedef struct {
  EosAppListModel *model;
  EosAppInfo *info;
  goffset current;
  goffset total;
} ProgressClosure;

static void
progress_closure_free (ProgressClosure *closure)
{
  g_object_unref (closure->model);
  g_object_unref (closure->info);
  g_slice_free (ProgressClosure, closure);
}

static ProgressClosure *
progress_closure_new (EosAppListModel *model,
                      EosAppInfo *info,
                      goffset current,
                      goffset total)
{
  ProgressClosure *closure = g_slice_new0 (ProgressClosure);
  closure->model = g_object_ref (model);
  closure->info = g_object_ref (info);
  closure->current = current;
  closure->total = total;

  return closure;
}

static gboolean
emit_download_progress_in_main_context (gpointer user_data)
{
  ProgressClosure *closure = user_data;
  eos_app_info_emit_download_progress (closure->info,
                                       closure->current, closure->total);

  return G_SOURCE_REMOVE;
}

static void
emit_download_progress (goffset current,
                        goffset total,
                        gpointer user_data)
{
  DownloadProgressCallbackData *data = user_data;

  /* Rate-limit download notifications */
  gint64 current_time = g_get_monotonic_time ();
  gint64 time_elapsed = current_time - data->last_notification;

  /* Always emit the last notification */
  if ((time_elapsed <= DOWNLOAD_RATE_LIMIT_MS * 1000) &&
      current != total)
    return;

  eos_app_log_debug_message ("Emitting download progress signal "
                             "(%" G_GOFFSET_FORMAT " "
                             "of %" G_GOFFSET_FORMAT ")",
                             current,
                             total);
  g_assert_nonnull (data->info);

  ProgressClosure *closure =
    progress_closure_new (data->model, data->info, current, total);

  data->last_notification = current_time;
  g_main_context_invoke_full (NULL, G_PRIORITY_DEFAULT,
                              emit_download_progress_in_main_context,
                              closure, (GDestroyNotify) progress_closure_free);
}

static gboolean
get_bundle_artifacts (EosAppListModel *self,
                      EosAppInfo *info,
                      char *transaction_path,
                      gboolean is_upgrade,
                      gboolean allow_deltas,
                      GCancellable *cancellable,
                      GError **error_out)
{
  gboolean use_delta = allow_deltas &&
                       is_upgrade &&
                       eos_app_info_get_has_delta_update (info);

  eos_app_log_info_message ("Accessing dbus transaction");

  g_autofree char *download_dir = NULL;
  g_autofree char *bundle_path = NULL;
  g_autofree char *signature_path = NULL;

  GError *error = NULL;
  g_autoptr(EosAppManagerTransaction) transaction =
    eos_app_manager_transaction_proxy_new_sync (self->system_bus,
                                                G_DBUS_PROXY_FLAGS_NONE,
                                                "com.endlessm.AppManager",
                                                transaction_path,
                                                cancellable,
                                                &error);
  g_dbus_proxy_set_default_timeout (G_DBUS_PROXY (transaction), G_MAXINT);

  gboolean retval = FALSE;

  if (error != NULL)
    {
      eos_app_log_error_message ("Getting dbus transaction failed: %s", error->message);
      goto out;
    }

  DownloadProgressCallbackData *data = g_slice_new0 (DownloadProgressCallbackData);
  data->model = g_object_ref (self);
  data->info = g_object_ref (info);

  eos_app_log_info_message ("Downloading bundle (use_delta: %s)",
                            use_delta ? "true" : "false");

  download_dir = eos_get_bundle_download_dir (eos_app_info_get_application_id (info),
                                              eos_app_info_get_available_version (info));

  bundle_path = eos_app_info_download_bundle (info, self->soup_session,
                                              download_dir,
                                              use_delta,
                                              cancellable,
                                              emit_download_progress, data,
                                              &error);
  download_progress_callback_data_free (data);

  if (error != NULL)
    {
      eos_app_log_error_message ("Download of bundle failed: %s", error->message);
      goto out;
    }

  eos_app_log_info_message ("Downloading signature");
  signature_path = eos_app_info_download_signature (info, self->soup_session,
                                                    download_dir,
                                                    use_delta,
                                                    cancellable, &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Signature download failed: %s", error->message);
      goto out;
    }

  eos_app_log_info_message ("Checking bundle checksum");
  const char *checksum = eos_app_info_get_checksum (info, use_delta, &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Checksum not available: %s", error->message);
      goto out;
    }

  if (!eos_app_utils_verify_checksum (bundle_path, checksum, &error))
    {
      eos_app_log_error_message ("Checksum failed: %s", error->message);
      goto out;
    }

  eos_app_log_info_message ("Completing transaction with eam");

  EosStorageType storage_type;

  if (is_upgrade)
    {
      /* Update to the location where the app currently is.
       * In case we don't have enough space on that location, the app
       * manager will return a failure.
       * In the future we probably want to be smarter and move things around
       * when an update is requested and free space is found on at least
       * one storage.
       */
      storage_type = eos_app_info_get_storage_type (info);
    }
  else
    storage_type = eos_app_info_get_install_storage_type (info);

  if (storage_type == EOS_STORAGE_TYPE_UNKNOWN)
    {
      eos_app_log_error_message ("Unable to determine where the bundle should be installed");

      g_set_error_literal (&error, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_DISK_FULL,
                           _("Not enough space on device for installing the app."));
      goto out;
    }

  GVariantBuilder opts;
  g_variant_builder_init (&opts, G_VARIANT_TYPE ("a{sv}"));
  g_variant_builder_add (&opts, "{sv}", "StorageType", g_variant_new_take_string (eos_storage_type_to_string (storage_type)));
  g_variant_builder_add (&opts, "{sv}", "BundlePath", g_variant_new_string (bundle_path));
  g_variant_builder_add (&opts, "{sv}", "SignaturePath", g_variant_new_string (signature_path));

  eos_app_manager_transaction_call_complete_transaction_sync (transaction,
                                                              g_variant_builder_end (&opts),
                                                              &retval,
                                                              cancellable,
                                                              &error);

out:
  if (error == NULL)
    {
      /* Delete the downloaded bundle and signature  but only if everything
       * went good with the download */
      if (bundle_path)
        g_unlink (bundle_path);
      if (signature_path)
        g_unlink (signature_path);
    }
  else
    {
      eos_app_log_error_message ("Completion of transaction %s failed",
                                 transaction_path);

      /* cancel the transaction on error */
      if (transaction != NULL)
        eos_app_manager_transaction_call_cancel_transaction_sync (transaction, NULL, NULL);

      /* The app manager uses InvalidFile for errors that deal with
       * bad input — invalid file, or wrong signature.
       *
       * It is harmful to leave these files around in the case when
       * the transaction fails with this error, because they may fool
       * the app store into not downloading them again until the next
       * change in the app version.
       *
       * On the app store side, we want to delete the files in case of
       * a mismatched checksum, which falls under the same category as
       * the InvalidFile error from the app manager.
       */
      g_autofree char *errmsg = g_dbus_error_get_remote_error (error);
      if (g_error_matches (error, EOS_APP_STORE_ERROR, EOS_APP_STORE_ERROR_CHECKSUM_MISSING) ||
          g_strcmp0 (errmsg, "com.endlessm.AppManager.Error.InvalidFile") == 0)
        {
          if (bundle_path)
            g_unlink (bundle_path);
          if (signature_path)
            g_unlink (signature_path);
        }

      /* Bubble the error up */
      g_propagate_error (error_out, error);

      retval = FALSE;
    }

  return retval;
}

static void
set_app_installation_error (const char *app_name,
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
      g_set_error_literal (error_out, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_INSTALL_FAILED,
                           _("We encountered an internal error during the installation of the application."));
    }
  else
    {
      g_set_error_literal (error_out, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_INSTALL_FAILED,
                           external_message);
    }
}

static void
set_app_uninstall_error (const char *app_name,
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
      g_set_error_literal (error_out, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_UNINSTALL_FAILED,
                           _("We encountered an internal error during the removal of the application."));
    }
  else
    {
      g_set_error_literal (error_out, EOS_APP_STORE_ERROR,
                           EOS_APP_STORE_ERROR_UNINSTALL_FAILED,
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
  const char *internal_message = NULL;
  const char *external_message = NULL;

  if (!self->can_install)
    {
      external_message = _("You must be an administrator to install applications.");
      goto out;
    }

  /* We do a double check here, to catch the case where the app manager
   * proxy was successfully created, but the app bundles directory was
   * removed afterwards
   */
  EosAppManager *proxy = eos_get_eam_dbus_proxy ();
  if (proxy == NULL ||
      !g_file_test (eos_get_bundles_dir (), G_FILE_TEST_EXISTS))
    {
      external_message = FATAL_ERROR_MESSAGE;
      goto out;
    }

  char *transaction_path = NULL;

  /* We use different DBus targets but everything else is same */
  if (is_upgrade)
    {
      eos_app_log_info_message ("Calling update dbus method with app_id: %s", app_id);
      eos_app_manager_call_update_sync (proxy, app_id,
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
            external_message = _("You must be an administrator to install applications.");

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

  retval = get_bundle_artifacts (self, info, transaction_path, is_upgrade, allow_deltas,
                                 cancellable, &error);

  if (error != NULL)
    {
      /* propagate only the errors we generate as they are... */
      if (error->domain == EOS_APP_STORE_ERROR)
        external_message = error->message;

      internal_message = error->message;
      goto out;
    }

  if (is_upgrade)
    /* When updating an application, GAppInfoMonitor might not send us a signal,
     * e.g. because no desktop files changed.
     * So we queue a refresh of the installed applications when we reach back
     * the main thread.
     */
    eos_app_list_model_queue_refresh_installed (self);

 out:
  if (!retval && !internal_message)
    internal_message = "Install transaction failed";

  if (!retval)
    set_app_installation_error (eos_app_info_get_title (info),
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
  gboolean allow_deltas = eos_use_delta_updates ();
  const char *desktop_id = eos_app_info_get_desktop_id (info);

  eos_app_log_info_message ("Attempting to update '%s' (deltas allowed: %s)",
                            desktop_id, allow_deltas ? "true" : "false");

  retval = install_latest_app_version (self,
                                       info,
                                       TRUE, /* Is update? */
                                       allow_deltas,
                                       cancellable,
                                       &error);

  /* Incremental update failed */
  if (!retval)
    {
      eos_app_log_info_message ("Update of '%s' (deltas allowed: %s) failed: %s",
                                desktop_id, allow_deltas ? "true" : "false",
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
  const char *internal_message = NULL;
  const char *external_message = NULL;

  if (!self->can_uninstall)
    {
      external_message = _("You must be an administrator to remove applications.");
      goto out;
    }

  /* We do a double check here, to catch the case where the app manager
   * proxy was successfully created, but the app bundles directory was
   * removed afterwards
   */
  EosAppManager *proxy = eos_get_eam_dbus_proxy ();
  if (proxy == NULL ||
      !g_file_test (eos_get_bundles_dir (), G_FILE_TEST_EXISTS))
    {
      external_message = FATAL_ERROR_MESSAGE;
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
            external_message = _("You must be an administrator to remove applications.");

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
    set_app_uninstall_error (eos_app_info_get_title (info),
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

  guint i, n_elements = json_array_get_length (model->content_apps);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (model->content_apps, i);

      JsonObject *obj = json_node_get_object (element);
      const char *category_id = json_object_get_string_member (obj, "category");
      EosAppCategory obj_category = eos_app_category_from_id (category_id);

      if (category == obj_category ||
          category == EOS_APP_CATEGORY_INSTALLED ||
          category == EOS_APP_CATEGORY_ALL)
        {
          const char *app_id = json_object_get_string_member (obj, "application-id");
          char *desktop_id = g_strconcat (app_id, ".desktop", NULL);

          EosAppInfo *info = eos_app_list_model_get_app_info (model, desktop_id);
          g_free (desktop_id);

          if (info != NULL)
            apps = g_list_prepend (apps, info);
        }
    }

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
                               EOS_APP_STORE_ERROR,
                               EOS_APP_STORE_ERROR_FAILED,
                               _("App %s has no candidate for installation."),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (eos_app_info_is_installed (info) &&
      eos_app_info_get_has_launcher (info))
    {
      g_task_return_new_error (task,
                               EOS_APP_STORE_ERROR,
                               EOS_APP_STORE_ERROR_INSTALLED,
                               _("App '%s' is already installed."),
                               eos_app_info_get_title (info));
      g_object_unref (task);
      return;
    }

  eos_app_info_set_is_installing (info, TRUE);

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, add_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_install_app_finish (EosAppListModel *model,
                                       GAsyncResult *result,
                                       GError **error)
{
  GTask *task = G_TASK (result);
  EosAppInfo *info = g_task_get_task_data (task);

  eos_app_info_set_is_installing (info, FALSE);

  return g_task_propagate_boolean (task, error);
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
                               EOS_APP_STORE_ERROR,
                               EOS_APP_STORE_ERROR_FAILED,
                               _("App %s not installable."),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (!eos_app_info_is_updatable (info))
    {
      g_task_return_new_error (task,
                               EOS_APP_STORE_ERROR,
                               EOS_APP_STORE_ERROR_NO_UPDATE_AVAILABLE,
                               _("App %s is up to date."),
                               eos_app_info_get_title (info));
      g_object_unref (task);
      return;
    }

  eos_app_info_set_is_updating (info, TRUE);

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, update_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_update_app_finish (EosAppListModel *model,
                                      GAsyncResult *result,
                                      GError **error)
{
  GTask *task = G_TASK (result);
  EosAppInfo *info = g_task_get_task_data (task);

  eos_app_info_set_is_updating (info, FALSE);

  return g_task_propagate_boolean (task, error);
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
      eos_app_log_error_message ("Unable to remove app '%s' from shell: %s",
                                 eos_app_info_get_application_id (info),
                                 error->message);
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
                               EOS_APP_STORE_ERROR,
                               EOS_APP_STORE_ERROR_NOT_INSTALLED,
                               _("App '%s' is not installed."),
                               info != NULL ? eos_app_info_get_title (info)
                                            : desktop_id);
      g_object_unref (task);
      return;
    }

  eos_app_info_set_is_removing (info, TRUE);

  g_task_set_task_data (task, g_object_ref (info), g_object_unref);
  g_task_run_in_thread (task, remove_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_uninstall_app_finish (EosAppListModel *model,
                                         GAsyncResult *result,
                                         GError **error)
{
  GTask *task = G_TASK (result);
  EosAppInfo *info = g_task_get_task_data (task);
  gboolean res = g_task_propagate_boolean (task, error);

  /* If we successfully removed the application, we wait for GIO
   * to notify us before we remove the flag.
   */
  if (!res)
    eos_app_info_set_is_removing (info, FALSE);

  return res;
}

gboolean
eos_app_list_model_launch_app (EosAppListModel *model,
                               const char *desktop_id,
                               guint32 timestamp,
                               GError **error)
{
  EosAppInfo *info = eos_app_list_model_get_app_info (model, desktop_id);

  if (info == NULL || !eos_app_info_is_installed (info))
    {
      g_set_error (error,
                   EOS_APP_STORE_ERROR,
                   EOS_APP_STORE_ERROR_NOT_INSTALLED,
                   _("App '%s' is not installed."),
                   info == NULL ? desktop_id : eos_app_info_get_title (info));
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

      g_hash_table_insert (model->apps, g_strdup (desktop_id), info);
    }

  eos_app_info_update_from_gio (info, desktop_info);
  g_object_unref (desktop_info);

  return info;
}
