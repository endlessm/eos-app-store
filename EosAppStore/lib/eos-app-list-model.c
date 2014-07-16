/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-list-model.h"

#include <glib-object.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <glib/gi18n-lib.h>

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *system_bus;
  GDBusConnection *session_bus;

  GAppInfoMonitor *app_monitor;

  GMutex table_lock;

  GHashTable *gio_apps;
  GHashTable *shell_apps;
  GHashTable *installed_apps;
  GHashTable *installable_apps;
  GHashTable *updatable_apps;

  guint applications_changed_id;
  guint available_apps_changed_id;

  gboolean can_install;
  gboolean can_uninstall;
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

G_DEFINE_TYPE (EosAppListModel, eos_app_list_model, G_TYPE_OBJECT)
G_DEFINE_QUARK (eos-app-list-model-error-quark, eos_app_list_model_error)

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
  return g_strndup (desktop_id, len - 8); /* the 8 here is the length of ".desktop" */
}

static gchar *
localized_id_from_desktop_id (const gchar *desktop_id)
{
  /* HACK: this should really be removed in favor of communicating the
   * language to the app manager API...
   */
  const gchar * const * locales;
  const gchar *locale_name;
  const gchar *lang_id;
  gchar **variants;
  gchar *localized_id;
  gchar *app_id;

  locales = g_get_language_names ();
  locale_name = locales[0];

  variants = g_get_locale_variants (locale_name);
  lang_id = variants[g_strv_length (variants) - 1];

  app_id = app_id_from_desktop_id (desktop_id);
  localized_id = g_strdup_printf ("%s-%s.desktop", app_id, lang_id);

  g_free (app_id);
  g_strfreev (variants);

  return localized_id;
}

static GHashTable *
load_shell_apps_from_gvariant (GVariant *apps)
{
  GHashTable *retval;
  GVariantIter *iter;
  gchar *application;

  retval = g_hash_table_new_full (g_str_hash, g_str_equal,
                                  g_free, NULL);

  g_variant_get (apps, "(as)", &iter);

  while (g_variant_iter_loop (iter, "s", &application))
    g_hash_table_add (retval, g_strdup (application));

  g_variant_iter_free (iter);

  return retval;
}

static GHashTable *
load_installable_apps_from_gvariant (GVariantIter *apps)
{
  GHashTable *retval;
  GVariantIter *iter;
  gchar *desktop_id, *id, *name, *version;

  retval = g_hash_table_new_full (g_str_hash, g_str_equal, g_free, NULL);

  iter = g_variant_iter_copy (apps);

  while (g_variant_iter_loop (iter, "(sss)", &id, &name, &version))
    {
      desktop_id = g_strdup_printf ("%s.desktop", id);
      g_hash_table_add (retval, desktop_id);
    }

  g_variant_iter_free (iter);

  return retval;
}

static void
on_app_monitor_changed (GAppInfoMonitor *monitor,
                        EosAppListModel *self)
{
  g_mutex_lock (&self->table_lock);

  if (self->gio_apps != NULL)
    {
      g_hash_table_unref (self->gio_apps);
      self->gio_apps = NULL;
    }

  g_mutex_unlock (&self->table_lock);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
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

  g_mutex_lock (&self->table_lock);

  g_clear_pointer (&self->shell_apps, g_hash_table_unref);
  self->shell_apps = load_shell_apps_from_gvariant (parameters);

  g_mutex_unlock (&self->table_lock);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
on_app_manager_available_applications_changed (GDBusConnection *connection,
                                               const gchar     *sender_name,
                                               const gchar     *object_path,
                                               const gchar     *interface_name,
                                               const gchar     *signal_name,
                                               GVariant        *parameters,
                                               gpointer         user_data)
{
  EosAppListModel *self = user_data;

  g_mutex_lock (&self->table_lock);

  g_clear_pointer (&self->installable_apps, g_hash_table_unref);
  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  GVariantIter *iter1, *iter2;

  g_variant_get (parameters, "(a(sss)a(sss))", &iter1, &iter2);

  self->installable_apps = load_installable_apps_from_gvariant (iter1);
  self->updatable_apps = load_installable_apps_from_gvariant (iter2);

  g_variant_iter_free (iter1);
  g_variant_iter_free (iter2);

  g_mutex_unlock (&self->table_lock);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  g_mutex_clear (&self->table_lock);

  if (self->applications_changed_id != 0)
    {
      g_dbus_connection_signal_unsubscribe (self->session_bus,
                                            self->applications_changed_id);
      self->applications_changed_id = 0;
    }

  if (self->available_apps_changed_id != 0)
    {
      g_dbus_connection_signal_unsubscribe (self->system_bus,
                                            self->available_apps_changed_id);
      self->available_apps_changed_id = 0;
    }

  g_clear_object (&self->app_monitor);
  g_clear_object (&self->session_bus);
  g_clear_object (&self->system_bus);

  g_hash_table_unref (self->gio_apps);
  g_hash_table_unref (self->shell_apps);
  g_hash_table_unref (self->installed_apps);
  g_hash_table_unref (self->updatable_apps);
  g_hash_table_unref (self->installable_apps);

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
}

static void
eos_app_list_model_init (EosAppListModel *self)
{
  g_mutex_init (&self->table_lock);

  self->system_bus = g_bus_get_sync (G_BUS_TYPE_SYSTEM, NULL, NULL);
  self->session_bus = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);

  self->app_monitor = g_app_info_monitor_get ();
  g_signal_connect (self->app_monitor, "changed",
                    G_CALLBACK (on_app_monitor_changed),
                    self);

  self->applications_changed_id =
    g_dbus_connection_signal_subscribe (self->session_bus,
                                        "org.gnome.Shell",
                                        "org.gnome.Shell.AppStore",
                                        "ApplicationsChanged",
                                        "/org/gnome/Shell",
                                        NULL, G_DBUS_SIGNAL_FLAGS_NONE,
                                        on_shell_applications_changed,
                                        self, NULL);

  self->available_apps_changed_id =
    g_dbus_connection_signal_subscribe (self->system_bus,
                                        "com.endlessm.AppManager",
                                        "com.endlessm.AppManager",
                                        "AvailableApplicationsChanged",
                                        "/com/endlessm/AppManager",
                                        NULL, G_DBUS_SIGNAL_FLAGS_NONE,
                                        on_app_manager_available_applications_changed,
                                        self, NULL);
}

EosAppListModel *
eos_app_list_model_new (void)
{
  return g_object_new (EOS_TYPE_APP_LIST_MODEL, NULL);
}

static gboolean
launch_app (EosAppListModel *self,
            const char *desktop_id,
            GCancellable *cancellable,
            GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;
  GVariant *res;

  res = g_dbus_connection_call_sync (self->session_bus,
                                     "org.gnome.Shell",
                                     "/org/gnome/Shell",
                                     "org.gnome.Shell.AppLauncher", "Launch",
                                     g_variant_new ("(s)", desktop_id),
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
                  const char *desktop_id,
                  GCancellable *cancellable,
                  GError **error_out)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->session_bus,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "AddApplication",
                               g_variant_new ("(s)", desktop_id),
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

static gboolean
add_app_from_manager (EosAppListModel *self,
                      const char *desktop_id,
                      GCancellable *cancellable,
                      GError **error_out)
{
  GError *error = NULL;
  gchar *app_id;

  app_id = app_id_from_desktop_id (desktop_id);
  g_dbus_connection_call_sync (self->system_bus,
                               "com.endlessm.AppManager",
                               "/com/endlessm/AppManager",
                               "com.endlessm.AppManager", "Install",
                               g_variant_new ("(s)", app_id),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               G_MAXINT,
                               NULL,
                               &error);
  g_free (app_id);

  if (error != NULL)
    {
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return TRUE;
}

static gboolean
remove_app_from_shell (EosAppListModel *self,
                       const char *desktop_id,
                       GCancellable *cancellable,
                       GError **error_out)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->session_bus,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "RemoveApplication",
                               g_variant_new ("(s)", desktop_id),
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
                         const char *desktop_id,
                         GCancellable *cancellable,
                         GError **error_out)
{
  GError *error = NULL;
  gchar *app_id;

  app_id = app_id_from_desktop_id (desktop_id);
  g_dbus_connection_call_sync (self->system_bus,
                               "com.endlessm.AppManager",
                               "/com/endlessm/AppManager",
                               "com.endlessm.AppManager", "Uninstall",
                               g_variant_new ("(s)", app_id),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               G_MAXINT,
                               cancellable,
                               &error);
  g_free (app_id);

  if (error != NULL)
    {
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return TRUE;
}

static gboolean
update_app_from_manager (EosAppListModel *self,
                         const char *desktop_id,
                         GCancellable *cancellable,
                         GError **error_out)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->system_bus,
                               "com.endlessm.AppManager",
                               "/com/endlessm/AppManager",
                               "com.endlessm.AppManager", "Install",
                               g_variant_new ("(s)", desktop_id),
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

static gboolean
app_is_visible (GAppInfo *info)
{
  GDesktopAppInfo *desktop_info = G_DESKTOP_APP_INFO (info);

  return !g_desktop_app_info_get_nodisplay (desktop_info) &&
    !g_desktop_app_info_get_is_hidden (desktop_info);
}

static void
load_apps_from_gio (EosAppListModel *self)
{
  GList *all_infos, *l;
  GAppInfo *info;
  GHashTable *set;

  g_clear_pointer (&self->gio_apps, g_hash_table_unref);

  all_infos = g_app_info_get_all ();
  set = g_hash_table_new_full (g_str_hash, g_str_equal,
                               NULL,
                               g_object_unref);

  for (l = all_infos; l != NULL; l = l->next)
    {
      info = l->data;

      if (app_is_visible (info))
        g_hash_table_insert (set, (gpointer) g_app_info_get_id (info), info);
      else
        g_object_unref (info);
    }

  g_list_free (all_infos);
  self->gio_apps = set;
}

static void
load_apps_from_shell (EosAppListModel *self)
{
  GVariant *applications;
  GError *error = NULL;

  g_clear_pointer (&self->shell_apps, g_hash_table_unref);

  applications =
    g_dbus_connection_call_sync (self->session_bus,
                                 "org.gnome.Shell",
                                 "/org/gnome/Shell",
                                 "org.gnome.Shell.AppStore",
                                 "ListApplications",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 NULL,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list applications: %s",
                  error->message);
      g_error_free (error);
      return;
    }

  self->shell_apps = load_shell_apps_from_gvariant (applications);
  g_variant_unref (applications);
}

static void
load_installed_apps (EosAppListModel *self)
{
  GVariant *applications;
  GError *error = NULL;

  g_clear_pointer (&self->installed_apps, g_hash_table_unref);

  applications =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager",
                                 "ListInstalled",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 NULL,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list installed applications: %s",
                  error->message);
      g_error_free (error);
      return;
    }

  GVariantIter *iter;

  g_variant_get (applications, "(a(sss))", &iter);

  self->installed_apps = load_installable_apps_from_gvariant (iter);

  g_variant_iter_free (iter);
  g_variant_unref (applications);
}

static void
load_available_apps (EosAppListModel *self)
{
  GVariant *applications;
  GError *error = NULL;

  g_clear_pointer (&self->installable_apps, g_hash_table_unref);
  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  applications =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager",
                                 "ListAvailable",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 NULL,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list available applications: %s",
                  error->message);
      g_error_free (error);
      return;
    }

  GVariantIter *iter1, *iter2;

  g_variant_get (applications, "(a(sss)a(sss))", &iter1, &iter2);

  self->installable_apps = load_installable_apps_from_gvariant (iter1);
  self->updatable_apps = load_installable_apps_from_gvariant (iter2);

  g_variant_iter_free (iter1);
  g_variant_iter_free (iter2);
  g_variant_unref (applications);
}

static void
load_user_capabilities (EosAppListModel *self)
{
  GVariant *capabilities;
  GError *error = NULL;

  capabilities =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager",
                                 "GetUserCapabilities",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 NULL,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list retrieve user capabilities: %s",
                  error->message);
      g_error_free (error);
      return;
    }


  GVariant *caps;
  caps = g_variant_get_child_value (capabilities, 0);

  g_variant_lookup (caps, "CanInstall", "b", &self->can_install);
  g_variant_lookup (caps, "CanUninstall", "b", &self->can_uninstall);

  g_variant_unref (caps);
  g_variant_unref (capabilities);
}

static void
all_apps_load_in_thread (GTask        *task,
                         gpointer      object,
                         gpointer      task_data,
                         GCancellable *cancellable)
{
  EosAppListModel *model = object;

  /* we acquire a lock on the tables here, since all these
   * functions are synchronous
   */

  g_mutex_lock (&model->table_lock);

  load_apps_from_gio (model);
  load_apps_from_shell (model);
  load_installed_apps (model);
  load_available_apps (model);
  load_user_capabilities (model);

  g_mutex_unlock (&model->table_lock);

  g_task_return_pointer (task, NULL, NULL);
}

/**
 * eos_app_list_model_load:
 * @model:
 * @cancellable: (allow-none):
 * @callback:
 * @user_data:
 *
 */
void
eos_app_list_model_load (EosAppListModel     *model,
                         GCancellable        *cancellable,
                         GAsyncReadyCallback  callback,
                         gpointer             user_data)
{
  GTask *task;

  g_return_if_fail (EOS_IS_APP_LIST_MODEL (model));
  g_return_if_fail (callback != NULL);

  task = g_task_new (model, cancellable, callback, user_data);
  g_task_run_in_thread (task, all_apps_load_in_thread);
  g_object_unref (task);
}

/**
 * eos_app_list_model_load_finish:
 * @model:
 * @result:
 * @error:
 *
 * Returns: (transfer container) (element-type utf8):
 */
GList *
eos_app_list_model_load_finish (EosAppListModel  *model,
                                GAsyncResult     *result,
                                GError          **error)
{
  GList *gio_apps = NULL;
  GList *installable_apps = NULL;

  g_return_val_if_fail (g_task_is_valid (result, model), NULL);

  if ((model->gio_apps == NULL && model->installable_apps == NULL) ||
      g_task_had_error (G_TASK (result)))
    return g_task_propagate_pointer (G_TASK (result), error);

  if (model->gio_apps)
    gio_apps = g_hash_table_get_keys (model->gio_apps);
  if (model->installable_apps)
    installable_apps = g_hash_table_get_keys (model->installable_apps);

  return g_list_concat (gio_apps, installable_apps);
}

/**
 * eos_app_list_model_get_app_info:
 * @model: the app list model
 * @desktop_id : the id of the app
 *
 * Returns the #GDesktopAppInfo for the given app.
 *
 * Returns: (transfer none): A #GDesktopAppInfo
 */
static GDesktopAppInfo *
eos_app_list_model_get_app_info (EosAppListModel *model,
                                 const char *desktop_id)
{
  gchar *override_desktop_id;
  GDesktopAppInfo *info;

  if (model->gio_apps == NULL)
    {
      g_critical ("The application list is not loaded.");
      return NULL;
    }

  override_desktop_id = g_strdup_printf ("eos-app-%s", desktop_id);
  info = g_hash_table_lookup (model->gio_apps, override_desktop_id);
  g_free (override_desktop_id);

  if (info == NULL)
    info = g_hash_table_lookup (model->gio_apps, desktop_id);

  if (info == NULL)
    {
      gchar *localized_id = localized_id_from_desktop_id (desktop_id);
      info = g_hash_table_lookup (model->gio_apps, localized_id);
      g_free (localized_id);
    }

  return info;
}

static gboolean
app_has_launcher (EosAppListModel *model,
                  const char      *desktop_id)
{
  /* Note that this doesn't mean that the application is installed */
  if (model->shell_apps == NULL)
    return FALSE;

  return g_hash_table_contains (model->shell_apps, desktop_id);
}

static gboolean
app_is_installable (EosAppListModel *model,
                    const char *desktop_id)
{
  if (model->installable_apps == NULL)
    return FALSE;

  return g_hash_table_contains (model->installable_apps, desktop_id);
}

static gchar *
app_get_localized_id_for_installable_app (EosAppListModel *model,
                                          const gchar *desktop_id)
{
  gchar *localized_id;

  if (desktop_id_is_web_link (desktop_id))
    return g_strdup (desktop_id);

  if (app_is_installable (model, desktop_id))
    return g_strdup (desktop_id);

  localized_id = localized_id_from_desktop_id (desktop_id);
  if (app_is_installable (model, localized_id))
    return localized_id;

  g_free (localized_id);
  return NULL;
}

static gboolean
app_is_manager_installed (EosAppListModel *model,
                          const char *desktop_id)
{
  if (model->installed_apps == NULL)
    return FALSE;

  return g_hash_table_lookup (model->installed_apps, desktop_id) != NULL;
}

static gboolean
app_is_updatable (EosAppListModel *model,
                  const char *desktop_id)
{
  if (model->updatable_apps == NULL)
    return FALSE;

  return g_hash_table_lookup (model->updatable_apps, desktop_id) != NULL;
}

static gboolean
app_is_installed (EosAppListModel *model,
                  const char      *desktop_id)
{
  /* An app is installed if GIO knows about it... */
  if (eos_app_list_model_get_app_info (model, desktop_id) != NULL)
    return TRUE;

  /* ...or if the app manager reports it as such */
  if (app_is_manager_installed (model, desktop_id))
    return TRUE;

  if (app_is_updatable (model, desktop_id))
    return TRUE;

  return FALSE;
}

static const gchar *
app_get_localized_id_for_installed_app (EosAppListModel *model,
                                        const gchar *desktop_id)
{
  GDesktopAppInfo *info;

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info != NULL)
    return g_app_info_get_id (G_APP_INFO (info));

  return NULL;
}

gboolean
eos_app_list_model_get_app_has_launcher (EosAppListModel *model,
                                         const char *desktop_id)
{
  const gchar *localized_id;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), FALSE);
  g_return_val_if_fail (desktop_id != NULL, FALSE);

  if (app_has_launcher (model, desktop_id))
    return TRUE;

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);
  return app_has_launcher (model, localized_id);
}

char *
eos_app_list_model_get_app_icon_name (EosAppListModel *model,
                                      const char *desktop_id)
{
  GDesktopAppInfo *info;
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (desktop_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    {
      /* TODO: for applications that are not on the system, just return
       * a hardcoded default for now. Eventually we want to get this information
       * from the server, through the app manager.
       */
      gchar *app_id = app_id_from_desktop_id (desktop_id);
      gchar *icon_name = g_strdup_printf ("eos-app-%s", app_id);
      g_free (app_id);

      return icon_name;
    }

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_ICON);
}

EosAppState
eos_app_list_model_get_app_state (EosAppListModel *model,
                                  const char *desktop_id)
{
  EosAppState retval = EOS_APP_STATE_UNKNOWN;
  gboolean is_installed;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), EOS_APP_STATE_UNKNOWN);
  g_return_val_if_fail (desktop_id != NULL, EOS_APP_STATE_UNKNOWN);

  is_installed = app_is_installed (model, desktop_id);

  if (is_installed && app_is_updatable (model, desktop_id))
    retval = EOS_APP_STATE_UPDATABLE;
  else if (is_installed)
    retval = EOS_APP_STATE_INSTALLED;
  else
    retval = EOS_APP_STATE_UNINSTALLED;

  return retval;
}

static void
add_app_thread_func (GTask *task,
                     gpointer source_object,
                     gpointer task_data,
                     GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  const gchar *desktop_id = task_data;

  g_mutex_lock (&model->table_lock);

  if (!app_is_installed (model, desktop_id))
    {
      if (!desktop_id_is_web_link (desktop_id) &&
          model->can_install &&
          !add_app_from_manager (model, desktop_id, cancellable, &error))
        {
          g_task_return_error (task, error);
          goto out;
        }
     }

  if (!app_has_launcher (model, desktop_id))
    {
      if (!add_app_to_shell (model, desktop_id, cancellable, &error))
        {
          g_task_return_error (task, error);
          goto out;
        }
    }

  g_hash_table_add (model->installed_apps, g_strdup (desktop_id));
  g_hash_table_add (model->shell_apps, g_strdup (desktop_id));

  g_task_return_boolean (task, TRUE);

out:
  g_mutex_unlock (&model->table_lock);
}

void
eos_app_list_model_install_app_async (EosAppListModel *model,
                                      const gchar *desktop_id,
                                      GCancellable *cancellable,
                                      GAsyncReadyCallback callback,
                                      gpointer user_data)
{
  GTask *task;
  char *localized_id;

  task = g_task_new (model, cancellable, callback, user_data);

  if (app_is_installed (model, desktop_id))
    localized_id = g_strdup (app_get_localized_id_for_installed_app (model, desktop_id));
  else
    localized_id = app_get_localized_id_for_installable_app (model, desktop_id);

  if (localized_id == NULL)
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_FAILED,
                               _("App %s not installable"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (app_is_installed (model, localized_id) && app_has_launcher (model, localized_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_INSTALLED,
                               _("App %s already installed"),
                               desktop_id);
      g_object_unref (task);
      g_free (localized_id);
      return;
    }

  g_task_set_task_data (task, localized_id, (GDestroyNotify) g_free);
  g_task_run_in_thread (task, add_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_install_app_finish (EosAppListModel *model,
                                       GAsyncResult *result,
                                       GError **error)
{
  GTask *task = G_TASK (result);

  if (!g_task_propagate_boolean (task, error))
    return FALSE;

  return TRUE;
}

static void
update_app_thread_func (GTask *task,
                        gpointer source_object,
                        gpointer task_data,
                        GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  const gchar *desktop_id = task_data;

  if (!update_app_from_manager (model, desktop_id, cancellable, &error))
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
  const char *localized_id;

  task = g_task_new (model, cancellable, callback, user_data);

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);

  if (localized_id == NULL)
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_FAILED,
                               _("App %s not installable"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (!app_is_updatable (model, localized_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                               _("App %s is up to date"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_set_task_data (task, g_strdup (localized_id), (GDestroyNotify) g_free);
  g_task_run_in_thread (task, update_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_update_app_finish (EosAppListModel *model,
                                      GAsyncResult *result,
                                      GError **error)
{
  GTask *task = G_TASK (result);

  if (!g_task_propagate_boolean (task, error))
    return FALSE;

  return TRUE;
}
static void
remove_app_thread_func (GTask *task,
                        gpointer source_object,
                        gpointer task_data,
                        GCancellable *cancellable)
{
  GError *error = NULL;
  EosAppListModel *model = source_object;
  const gchar *desktop_id = task_data;

  g_mutex_lock (&model->table_lock);

  if (model->can_uninstall && !remove_app_from_manager (model, desktop_id, cancellable, &error))
    {
      g_task_return_error (task, error);
      goto out;
    }

  if (!remove_app_from_shell (model, desktop_id, cancellable, &error))
    {
      g_task_return_error (task, error);
      goto out;
    }

  g_hash_table_remove (model->installed_apps, desktop_id);
  g_hash_table_remove (model->shell_apps, desktop_id);

  g_task_return_boolean (task, TRUE);

out:
  g_mutex_unlock (&model->table_lock);
}

void
eos_app_list_model_uninstall_app_async (EosAppListModel *model,
                                        const gchar *desktop_id,
                                        GCancellable *cancellable,
                                        GAsyncReadyCallback callback,
                                        gpointer user_data)
{
  GTask *task;
  const gchar *localized_id;

  task = g_task_new (model, cancellable, callback, user_data);

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);

  if ((localized_id == NULL) || !app_is_installed (model, localized_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NOT_INSTALLED,
                               _("App %s is not installed"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_set_task_data (task, g_strdup (localized_id), (GDestroyNotify) g_free);
  g_task_run_in_thread (task, remove_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_uninstall_app_finish (EosAppListModel *model,
                                         GAsyncResult *result,
                                         GError **error)
{
  GTask *task = G_TASK (result);

  if (!g_task_propagate_boolean (task, error))
    return FALSE;

  return TRUE;
}

gboolean
eos_app_list_model_launch_app (EosAppListModel *model,
                               const char *desktop_id,
                               GError **error)
{
  const gchar *localized_id;

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);

  if ((localized_id == NULL) || !app_is_installed (model, localized_id))
    {
      g_set_error (error,
                   eos_app_list_model_error_quark (),
                   EOS_APP_LIST_MODEL_ERROR_NOT_INSTALLED,
                   _("App %s is not installed"),
                   desktop_id);
      return FALSE;
    }

  return launch_app (model, localized_id, NULL, error);
}

gboolean
eos_app_list_model_has_app (EosAppListModel *model,
                            const char *desktop_id)
{
  gchar *localized_id;
  gboolean res = FALSE;

  g_mutex_lock (&model->table_lock);

  if (eos_app_list_model_get_app_info (model, desktop_id) != NULL)
    {
      res = TRUE;
      goto out;
    }

  if (app_is_installable (model, desktop_id))
    {
      res = TRUE;
      goto out;
    }

  localized_id = localized_id_from_desktop_id (desktop_id);
  res = app_is_installable (model, localized_id);
  g_free (localized_id);

out:
  g_mutex_unlock (&model->table_lock);

  return res;
}
