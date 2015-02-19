/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 et!: */

#include "config.h"

#include "eos-app-log.h"
#include "eos-app-list-model.h"
#include "eos-app-manager-service.h"
#include "eos-app-manager-transaction.h"

#include <glib-object.h>
#include <glib/gstdio.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <glib/gi18n-lib.h>
#include <libsoup/soup.h>

/* The delay for the EosAppListModel::changed signal, in milliseconds */
#define CHANGED_DELAY   500

/* Amount of seconds that we should keep retrying to download the file after
 * first interruption
 */
#define MAX_DOWNLOAD_RETRY_PERIOD 20

/* Amount of seconds that we should wait before retrying a failed download */
#define DOWNLOAD_RETRY_PERIOD 4

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *system_bus;
  GDBusConnection *session_bus;

  GAppInfoMonitor *app_monitor;

  GHashTable *gio_apps;
  GHashTable *shell_apps;
  GHashTable *apps;
  GHashTable *updatable_apps;
  GHashTable *manager_installed_apps;
  GHashTable *manager_removable_apps;

  GCancellable *load_cancellable;

  guint applications_changed_id;
  guint available_apps_changed_id;
  guint changed_guard_id;

  gboolean can_install;
  gboolean can_uninstall;

  SoupSession *soup_session;

  EosAppManager *proxy;
};

struct _EosAppListModelClass
{
  GObjectClass parent_class;
};

struct _EosAppListModelItem {
  char  *desktop_id;
  char  *name;
  char  *version;
  gint64 installed_size;

  EosAppState state;
};

typedef struct _EosAppListModelItem EosAppListModelItem;

/* TODO: Add consts for all apps info update types */
enum {
  EOS_APP_INFO_UPDATE_TYPE_INSTALLABLE
} _EosAppInfoUpdateType;

typedef enum _EosAppInfoUpdateType EosAppInfoUpdateType;

enum {
  CHANGED,
  DOWNLOAD_PROGRESS,

  LAST_SIGNAL
};

static guint eos_app_list_model_signals[LAST_SIGNAL] = { 0, };

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
    self->changed_guard_id = g_timeout_add (CHANGED_DELAY, emit_queued_changed, self);
}

#define WEB_LINK_ID_PREFIX "eos-link-"

static gboolean load_manager_installed_apps (EosAppListModel *self,
                                             GCancellable *cancellable);

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
get_language_id (void)
{
  const gchar * const * locales;
  const gchar *locale_name;
  gchar *lang_id;
  gchar **variants;

  locales = g_get_language_names ();
  locale_name = locales[0];

  variants = g_get_locale_variants (locale_name);
  lang_id = g_strdup_printf ("-%s", variants[g_strv_length (variants) - 1]);
  g_strfreev (variants);

  return lang_id;
}

static gchar *
unlocalized_desktop_id_from_app_id (const gchar *app_id)
{
  gchar *lang_id;
  gchar *unlocalized_app_id;
  gchar *retval;

  lang_id = get_language_id ();
  if (g_str_has_suffix (app_id, lang_id))
    unlocalized_app_id = g_strndup (app_id, strlen (app_id) - strlen (lang_id));
  else
    unlocalized_app_id = g_strdup (app_id);

  retval = g_strconcat (unlocalized_app_id, ".desktop", NULL);

  g_free (lang_id);
  g_free (unlocalized_app_id);

  return retval;
}

static gchar *
localized_id_from_desktop_id (const gchar *desktop_id)
{
  /* HACK: this should really be removed in favor of communicating the
   * language to the app manager API...
   */
  gchar *localized_id;
  gchar *app_id;
  gchar *lang_id;

  lang_id = get_language_id ();
  app_id = app_id_from_desktop_id (desktop_id);
  localized_id = g_strdup_printf ("%s%s.desktop", app_id, lang_id);

  g_free (app_id);
  g_free (lang_id);

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
create_app_hash_from_gvariant (GVariantIter *apps)
{
  GHashTable *retval;
  GVariantIter *iter;
  gchar *desktop_id, *id, *name, *version;
  gint64 installed_size;

  retval = g_hash_table_new_full (g_str_hash, g_str_equal, g_free, NULL);

  iter = g_variant_iter_copy (apps);

  while (g_variant_iter_loop (iter, "(sssx)", &id, &name, &version, &installed_size))
    {
      desktop_id = g_strdup_printf ("%s.desktop", id);
      g_hash_table_add (retval, desktop_id);
    }

  g_variant_iter_free (iter);

  return retval;
}

static gboolean
app_is_visible (GAppInfo *info)
{
  GDesktopAppInfo *desktop_info = G_DESKTOP_APP_INFO (info);

  return !g_desktop_app_info_get_nodisplay (desktop_info) &&
    !g_desktop_app_info_get_is_hidden (desktop_info);
}

static GHashTable *
load_apps_from_gio (void)
{
  GList *all_infos, *l;
  GAppInfo *info;
  GHashTable *set;

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
  return set;
}

static void
load_manager_installed_apps_thread_func (GTask *task,
                                         gpointer source_object,
                                         gpointer task_data,
                                         GCancellable *cancellable)
{
  EosAppListModel *self = source_object;
  GError *error = NULL;

  if (!load_manager_installed_apps (self, cancellable))
    {
      g_set_error_literal (&error, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                           "Unable to refresh the applications list");
      g_task_return_error (task, error);
      return;
    }

  g_task_return_boolean (task, TRUE);
}

static void
load_manager_installed_apps_async (EosAppListModel *self,
                                   GCancellable *cancellable,
                                   GAsyncReadyCallback callback,
                                   gpointer user_data)
{
  GTask *task = g_task_new (self, cancellable, callback, user_data);
  g_task_run_in_thread (task, load_manager_installed_apps_thread_func);
  g_object_unref (task);
}

static gboolean
load_manager_installed_apps_finish (EosAppListModel *self,
                                    GAsyncResult *res,
                                    GError **error)
{
  return g_task_propagate_boolean (G_TASK (res), error);
}

static void
on_load_installed_apps (GObject *obj,
                        GAsyncResult *res,
                        gpointer data G_GNUC_UNUSED)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (obj);
  GError *error = NULL;

  if (!load_manager_installed_apps_finish (self, res, &error))
    {
      g_warning ("%s", error->message);
      g_error_free (error);
      return;
    }

  eos_app_list_model_emit_changed (self);
}

static void
on_app_monitor_changed (GAppInfoMonitor *monitor,
                        EosAppListModel *self)
{
  g_clear_pointer (&self->gio_apps, g_hash_table_unref);
  self->gio_apps = load_apps_from_gio ();

  /* queue a reload of the manager-installed apps */
  load_manager_installed_apps_async (self, NULL, on_load_installed_apps, NULL);
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

  g_clear_pointer (&self->shell_apps, g_hash_table_unref);
  self->shell_apps = load_shell_apps_from_gvariant (parameters);

  eos_app_list_model_emit_changed (self);
}

static void
update_apps_info_item (GHashTable *apps,
                       char *desktop_id,
                       char *name,
                       char *version,
                       EosAppState state,
                       gint64 installed_size)
{
  EosAppListModelItem *apps_item_info = NULL;

  if (!g_hash_table_lookup_extended (apps, desktop_id, NULL, NULL)) {
    apps_item_info = g_slice_new0 (EosAppListModelItem);

    /* All 0s might not set the val to 0 on a signed int64 */
    apps_item_info->installed_size = 0;

    char *hash_key = g_strdup (desktop_id);

    g_hash_table_insert (apps, hash_key, apps_item_info);
  }

  /* We re-retrieve the pointer to ensure that it is in the list correctly */
  apps_item_info = g_hash_table_lookup (apps, desktop_id);

  apps_item_info->desktop_id = g_strdup (desktop_id);

  /* Update properties if needed on the item */
  if (name != NULL)
    apps_item_info->name = g_strdup (name);

  if (version != NULL)
    apps_item_info->version = g_strdup (version);

  if (apps_item_info->installed_size > 0)
    apps_item_info->installed_size = installed_size;

  /* Update state flag based on the type of update */
  apps_item_info->state = state;
}

/* Used to free the model-apps values */
static void
destroy_app_list_model_item (gpointer data)
{
  EosAppListModelItem *item = (EosAppListModelItem *) data;

  g_free (item->desktop_id);
  g_free (item->name);
  g_free (item->version);

  g_slice_free (EosAppListModelItem, item);
}

static void
update_apps_info_from_gvariant (EosAppListModel *self,
                                GVariantIter *apps,
                                EosAppState state)
{
  gchar *desktop_id, *id, *name, *version;
  gint64 installed_size;

  GVariantIter *iter;

  iter = g_variant_iter_copy (apps);

  /* Create our master app list if we don't have one */
  if (self->apps == NULL)
    self->apps = g_hash_table_new_full (g_str_hash,
                                        g_str_equal,
                                        g_free,
                                        destroy_app_list_model_item);

  while (g_variant_iter_loop (iter, "(sssx)", &id, &name, &version, &installed_size))
    {
      desktop_id = g_strdup_printf ("%s.desktop", id);

      update_apps_info_item (self->apps, desktop_id, name, version,
                             state,
                             installed_size);

      g_free (desktop_id);
    }

  g_free (id);
  g_free (name);
  g_free (version);

  g_variant_iter_free (iter);
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

  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  GVariantIter *iter1, *iter2;

  g_variant_get (parameters, "(a(sssx)a(sssx))", &iter1, &iter2);

  update_apps_info_from_gvariant (self, iter1, EOS_APP_STATE_AVAILABLE);

  self->updatable_apps = create_app_hash_from_gvariant (iter2);

  g_variant_iter_free (iter1);
  g_variant_iter_free (iter2);

  eos_app_list_model_emit_changed (self);
}

static gboolean
load_available_apps (EosAppListModel *self,
                     GHashTable **updatable_apps_out,
                     GCancellable *cancellable,
                     GError **error_out)
{
  GVariant *installable_apps = NULL;
  GVariant *updatable_apps = NULL;

  GError *error = NULL;

  const char * const *locales = g_get_language_names ();
  const char *locale_name = locales[0];

  char **variants = g_get_locale_variants (locale_name);
  const char *lang_id = variants[g_strv_length (variants) - 1];

  GVariantBuilder filter_builder;

  g_variant_builder_init (&filter_builder, G_VARIANT_TYPE ("a{sv}"));
  g_variant_builder_open (&filter_builder, G_VARIANT_TYPE ("a{sv}"));
  g_variant_builder_add (&filter_builder,
                         "{sv}",
                         "Locale",
                         g_variant_new_string (lang_id));
  g_variant_builder_close (&filter_builder);

  g_strfreev (variants);

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      eos_app_log_error_message ("Could not get DBus proxy object - canceling");

      return FALSE;
    }

  eos_app_log_info_message ("Trying to get available apps");

  eos_app_manager_call_list_available_sync (proxy,
                                            g_variant_builder_end (&filter_builder),
                                            &installable_apps,
                                            &updatable_apps,
                                            cancellable,
                                            &error);

  eos_app_log_info_message ("Retrieved available apps from eam manager");

  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to list available applications: %s",
                                 error->message);
      g_critical ("Unable to list available applications: %s",
                  error->message);

      g_propagate_error (error_out, error);

      return FALSE;
    }

  GVariantIter *installable_apps_iter, *updatable_apps_iter;
  g_variant_get (installable_apps, "a(sssx)", &installable_apps_iter);
  g_variant_get (updatable_apps, "a(sssx)", &updatable_apps_iter);

  eos_app_log_debug_message ("Parsing installable app list");
  update_apps_info_from_gvariant (self, installable_apps_iter, EOS_APP_STATE_AVAILABLE);

  eos_app_log_debug_message ("Parsing updatable app list");
  if (updatable_apps_out != NULL)
    *updatable_apps_out = create_app_hash_from_gvariant (updatable_apps_iter);

  eos_app_log_debug_message ("Done retrieving installed apps");

  g_variant_iter_free (installable_apps_iter);
  g_variant_iter_free (updatable_apps_iter);

  g_variant_unref (installable_apps);
  g_variant_unref (updatable_apps);

  return TRUE;
}

static gboolean
load_user_capabilities (EosAppListModel *self,
                        GCancellable *cancellable,
                        GError **error_out)
{
  GVariant *capabilities;
  GError *error = NULL;

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      eos_app_log_error_message ("Could not get DBus proxy object - canceling");

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
      g_critical ("Unable to list retrieve user capabilities: %s",
                  error->message);

      g_propagate_error (error_out, error);

      return FALSE;
    }

  g_variant_lookup (capabilities, "CanInstall", "b", &self->can_install);
  g_variant_lookup (capabilities, "CanUninstall", "b", &self->can_uninstall);
  g_variant_unref (capabilities);

  eos_app_log_debug_message ("CanInstall: %s",
                             self->can_install ? "Yes" : "No");
  eos_app_log_debug_message ("CanUninstall: %s",
                             self->can_uninstall ? "Yes" : "No");

  return TRUE;
}

static gboolean
load_manager_available_apps (EosAppListModel *self,
                             GCancellable *cancellable)
{
  GError *error = NULL;
  GHashTable *updatable_apps;

  if (!load_available_apps (self, &updatable_apps, cancellable, &error))
    goto out;

  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  self->updatable_apps = updatable_apps;

  if (!load_user_capabilities (self, cancellable, &error))
    goto out;

out:
  if (error != NULL)
    {
      g_critical ("Unable to list available apps: %s", error->message);
      g_error_free (error);
      return FALSE;
    }

  return TRUE;
}

static gboolean
load_manager_installed_apps (EosAppListModel *self,
                             GCancellable *cancellable)
{
  GVariant *installed_apps = NULL;
  GVariant *removable_apps = NULL;

  GError *error = NULL;

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      eos_app_log_error_message ("Could not get DBus proxy object - canceling");

      return FALSE;
    }

  eos_app_log_info_message ("Trying to get installed apps");

  eos_app_manager_call_list_installed_sync (proxy,
                                            &installed_apps,
                                            &removable_apps,
                                            cancellable,
                                            &error);

  eos_app_log_info_message ("Retrieved installed apps from eam manager");

  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to list installed applications: %s",
                                 error->message);
      g_critical ("Unable to list installed applications: %s", error->message);

      g_error_free (error);

      return FALSE;
    }

  eos_app_log_debug_message ("Parsing installed app return bjects");

  GVariantIter *installed_apps_iter, *removable_apps_iter;
  g_variant_get (installed_apps, "a(sssx)", &installed_apps_iter);
  g_variant_get (removable_apps, "a(sssx)", &removable_apps_iter);

  g_clear_pointer (&self->manager_installed_apps, g_hash_table_unref);
  g_clear_pointer (&self->manager_removable_apps, g_hash_table_unref);

  eos_app_log_debug_message ("Parsing installed app list");
  self->manager_installed_apps = create_app_hash_from_gvariant (installed_apps_iter);

  eos_app_log_debug_message ("Parsing removable app list");
  self->manager_removable_apps = create_app_hash_from_gvariant (removable_apps_iter);

  eos_app_log_debug_message ("Done retrieving installed apps");

  g_variant_iter_free (installed_apps_iter);
  g_variant_iter_free (removable_apps_iter);

  g_variant_unref (installed_apps);
  g_variant_unref (removable_apps);

  return TRUE;
}

static gboolean
load_shell_apps (EosAppListModel *self,
                 GCancellable *cancellable)
{
  GError *error = NULL;

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

  g_clear_pointer (&self->shell_apps, g_hash_table_unref);
  self->shell_apps = load_shell_apps_from_gvariant (applications);
  g_variant_unref (applications);

  return TRUE;
}

static gboolean
load_all_apps (EosAppListModel *self,
               GCancellable *cancellable,
               GError **error)
{
  eos_app_log_debug_message ("Loading GIO apps");
  g_clear_pointer (&self->gio_apps, g_hash_table_unref);
  self->gio_apps = load_apps_from_gio ();

  eos_app_log_debug_message ("Loading installed apps from manager");
  if (!load_manager_installed_apps (self, cancellable))
    goto out;

  eos_app_log_debug_message ("Loading available apps from manager");
  if (!load_manager_available_apps (self, cancellable))
    goto out;

  /* Load apps with launcher from the shell */
  eos_app_log_debug_message ("Loading apps with launcher from the shell");
  if (!load_shell_apps (self, cancellable))
    goto out;

  return TRUE;

out:
  g_set_error_literal (error, EOS_APP_LIST_MODEL_ERROR,
                       EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                       _("We were unable to update the list of applications"));

  return FALSE;
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  if (self->load_cancellable != NULL)
    g_cancellable_cancel (self->load_cancellable);

  g_clear_object (&self->load_cancellable);

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

  g_object_unref (&self->proxy);

  g_clear_object (&self->soup_session);
  g_clear_object (&self->app_monitor);
  g_clear_object (&self->session_bus);
  g_clear_object (&self->system_bus);

  g_hash_table_unref (self->gio_apps);
  g_hash_table_unref (self->shell_apps);
  g_hash_table_unref (self->updatable_apps);
  g_hash_table_unref (self->apps);
  g_hash_table_unref (self->manager_installed_apps);
  g_hash_table_unref (self->manager_removable_apps);

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

  self->available_apps_changed_id =
    g_dbus_connection_signal_subscribe (self->system_bus,
                                        "com.endlessm.AppManager",
                                        "com.endlessm.AppManager",
                                        "AvailableApplicationsChanged",
                                        "/com/endlessm/AppManager",
                                        NULL, G_DBUS_SIGNAL_FLAGS_NONE,
                                        on_app_manager_available_applications_changed,
                                        self, NULL);

  self->app_monitor = g_app_info_monitor_get ();
  g_signal_connect (self->app_monitor, "changed",
                    G_CALLBACK (on_app_monitor_changed),
                    self);
}

EosAppListModel *
eos_app_list_model_new (void)
{
  return g_object_new (EOS_TYPE_APP_LIST_MODEL, NULL);
}

static gboolean
refresh_app_manager (EosAppListModel *self,
                     GCancellable *cancellable,
                     GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;

  eos_app_log_info_message ("Refresh of apps requested");

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      eos_app_log_error_message ("Could not get DBus proxy object - canceling");

      return FALSE;
    }

  eos_app_log_info_message ("Trying to refresh app list");

  eos_app_manager_call_refresh_sync (proxy, &retval, NULL, &error);

  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to refresh the list of applications: %s",
                                 error->message);
      g_warning ("Unable to refresh the list of applications: %s",
                 error->message);
      g_error_free (error);
      retval = FALSE;
      goto out;
    }

out:
  if (!retval)
    {
      eos_app_log_error_message ("Unable to get the list of applications");

      g_set_error_literal (error_out, EOS_APP_LIST_MODEL_ERROR,
                           EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
                           _("We were unable to update the list of applications"));
    }

  eos_app_log_info_message ("Refresh apps: %s", retval ? "OK" : "Fail");

  return retval;
}

static void
refresh_thread_func (GTask *task,
                     gpointer source_object,
                     gpointer task_data,
                     GCancellable *cancellable)
{
  EosAppListModel *model = source_object;
  GError *error = NULL;

  /* we want refreshing from the app manager to be an optional
   * step, in case we don't have connectivity and we cannot
   * refresh the list of updates.
   */
  if (!refresh_app_manager (model, cancellable, &error))
    {
      g_warning ("Unable to refresh applications from the manager: %s",
                 error->message);
      g_clear_error (&error);
    }

  /* on the other hand, if we had an error loading the installed
   * apps, then we really want to return an error
   */
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
            const char *desktop_id,
            guint32 timestamp,
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

typedef void (* ProgressReportFunc) (const char *app_id,
                                     goffset current,
                                     goffset total,
                                     gpointer user_data);

typedef struct {
  EosAppListModel *model;
  char *desktop_id;
  goffset current;
  goffset total;
} ProgressClosure;

static void
progress_closure_free (gpointer _data)
{
  ProgressClosure *data = _data;

  g_clear_object (&data->model);
  g_free (data->desktop_id);

  g_slice_free (ProgressClosure, data);
}

static gboolean
emit_download_progress (gpointer _data)
{
  ProgressClosure *data = _data;

  g_signal_emit (data->model, eos_app_list_model_signals[DOWNLOAD_PROGRESS], 0,
                 data->desktop_id,
                 data->current,
                 data->total);

  return G_SOURCE_REMOVE;
}

static void
queue_download_progress (const char      *app_id,
                         goffset          current,
                         goffset          total,
                         gpointer         user_data)
{
  EosAppListModel *self = user_data;
  ProgressClosure *clos = g_slice_new (ProgressClosure);

  clos->model = g_object_ref (self);
  clos->desktop_id = unlocalized_desktop_id_from_app_id (app_id);
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

  if (path == NULL) {
    eos_app_log_error_message ("File doesn't exist");
  }

  eos_app_log_info_message ("Trying to get filesystem info from %s",
                            g_file_get_path(path));

  info = g_file_query_filesystem_info (path, G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                       cancellable,
                                       error);
  if (info == NULL) {
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

static gboolean
download_file_from_uri (EosAppListModel *self,
                        const char      *app_id,
                        const char      *source_uri,
                        const char      *target_file,
                        ProgressReportFunc progress_func,
                        gpointer         progress_func_user_data,
                        gboolean        *reset_error_counter,
                        GCancellable    *cancellable,
                        GError         **error)
{
  GError *internal_error = NULL;
  gboolean retval = FALSE;

  /* We assume that we won't get any data from the endpoint */
  *reset_error_counter = FALSE;

  SoupURI *uri = soup_uri_new (source_uri);

  if (uri == NULL)
    {
      eos_app_log_error_message ("Soap URI is NULL - canceling download");

      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
                   _("No available bundle for '%s'"),
                   app_id);
      return FALSE;
    }

  if (self->soup_session == NULL) {
    eos_app_log_error_message ("Creating new soup session");

    self->soup_session = soup_session_new ();
  }

  SoupRequest *request = soup_session_request_uri (self->soup_session, uri, &internal_error);

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

      return FALSE;
    }

  GByteArray *content = NULL;
  GFileOutputStream *out_stream = NULL;
  GInputStream *in_stream = soup_request_send (request, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Soup request sending had an internal error");

      g_propagate_error (error, internal_error);
      g_object_unref (request);
      return FALSE;
    }

  goffset total = soup_request_get_content_length (request);

  GFile *file = g_file_new_for_path (target_file);
  GFile *parent = g_file_get_parent (file);

  char *parent_path = g_file_get_path (parent);
  g_mkdir_with_parents (parent_path, 0755);
  g_free (parent_path);

  if (!check_available_space (parent, total, cancellable, &internal_error))
    {
      eos_app_log_error_message("Not enough space on FS - canceling download");

      g_propagate_error (error, internal_error);
      goto out;
    }

  /* we don't use GFile API because the error handling is weird,
   * and we also know that the target is a local file, so there
   * is no point in going through the abstraction
   */
  g_unlink (target_file);

  out_stream = g_file_create (file, G_FILE_CREATE_NONE, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      eos_app_log_error_message ("Create file failed - canceling download");

      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_FAILED,
                   _("Unable to create the file for downloading '%s': %s"),
                   app_id,
                   internal_error->message);
      g_error_free (internal_error);
      goto out;
    }

#define GET_DATA_BLOCK_SIZE     64 * 1024

  /* ensure we emit a progress notification at the beginning */
  if (progress_func != NULL)
    progress_func (app_id, 0, total, progress_func_user_data);

  gssize res = 0;
  gsize pos = 0;
  content = g_byte_array_new ();
  g_byte_array_set_size (content, GET_DATA_BLOCK_SIZE);

  eos_app_log_info_message ("Downloading file chunks start");

  /* we don't use splice() because it does not have progress, and the
   * data is coming from a network request, so it won't have a file
   * descriptor we can use splice() on
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
          eos_app_log_error_message ("Downloading file failed during piecewise"
                                     "transfer");

          g_propagate_error (error, internal_error);
          goto out;
        }

      pos += res;

      /* Since we got some data, we can assume that network is back online */
      *reset_error_counter = TRUE;

      if (progress_func != NULL)
        progress_func (app_id, pos, total, progress_func_user_data);
    }

  if (g_cancellable_is_cancelled (cancellable))
    {
      eos_app_log_info_message ("Canceled download");

      /* emit a progress notification for the whole file */
      if (progress_func != NULL)
        progress_func (app_id, total, total, progress_func_user_data);

      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_CANCELLED,
                   _("Download of app '%s' cancelled by the user."),
                   app_id);

      goto out;
    }

  if (res < 0)
    {
      g_propagate_error (error, internal_error);
      goto out;
    }

  /* ensure we emit a progress notification for the whole size */
  if (progress_func != NULL)
    progress_func (app_id, total, total, progress_func_user_data);

  retval = TRUE;

  eos_app_log_info_message ("Exiting download method normally");

out:
  g_clear_pointer (&content, g_byte_array_unref);
  g_clear_object (&file);
  g_clear_object (&parent);
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);

#undef GET_DATA_BLOCK_SIZE

  return retval;
}

static gboolean
download_file_from_uri_with_retry (EosAppListModel *self,
                                   const char      *app_id,
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
    while (TRUE) {
        download_success = download_file_from_uri (self, app_id, source_uri,
                                                   target_file,
                                                   progress_func,
                                                   progress_func_user_data,
                                                   &reset_error_counter,
                                                   cancellable,
                                                   &error);

        /* We're done if we get the file or we're canceled so exit the loop */
        if (download_success)
            break;

        eos_app_log_error_message ("Error downloading. Checking if retries are needed");

        if (reset_error_counter) {
            eos_app_log_info_message ("Some data retrieved during download failure. "
                                      "Resetting retry timeouts.");
            error_retry_cutoff = 0;
        }

        /* If this is our first retry, record the start time */
        if (error_retry_cutoff == 0)
            error_retry_cutoff = g_get_monotonic_time () + retry_time_limit;

        /* If we reached our limit of retry time, exit */
        if (g_get_monotonic_time () >= error_retry_cutoff) {
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
                  EosAppManagerTransaction *transaction,
                  const char *bundle_path,
                  GCancellable *cancellable,
                  GError **error_out)
{
  GError *error = NULL;
  const char *bundle_hash = eos_app_manager_transaction_get_bundle_hash (transaction);
  const char *app_id = eos_app_manager_transaction_get_application_id (transaction);

  if (bundle_hash == NULL || *bundle_hash == '\0')
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
                   _("No verification available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *sha256_name = g_strconcat (app_id, ".sha256", NULL);
  char *sha256_path = g_build_filename (BUNDLEDIR, sha256_name, NULL);
  g_free (sha256_name);

  gchar *contents = g_strconcat (bundle_hash, "\t", bundle_path, "\n", NULL);
  if (!g_file_set_contents (sha256_path, contents, -1, &error))
    g_propagate_error (error_out, error);

  g_free (contents);

  return sha256_path;
}

static char *
download_signature (EosAppListModel *self,
                    EosAppManagerTransaction *transaction,
                    GCancellable *cancellable,
                    GError **error_out)
{
  GError *error = NULL;
  const char *signature_uri = eos_app_manager_transaction_get_signature_uri (transaction);
  const char *app_id = eos_app_manager_transaction_get_application_id (transaction);

  if (signature_uri == NULL || *signature_uri == '\0')
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_INVALID_URL,
                   _("No signature available for app '%s'"),
                   app_id);
      return NULL;
    }

  char *signature_name = g_strconcat (app_id, ".asc", NULL);
  char *signature_path = g_build_filename (BUNDLEDIR, signature_name, NULL);
  g_free (signature_name);

  if (!download_file_from_uri_with_retry (self, app_id,
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
                 EosAppManagerTransaction *transaction,
                 GCancellable *cancellable,
                 GError **error_out)
{
  GError *error = NULL;
  const char *bundle_uri = eos_app_manager_transaction_get_bundle_uri (transaction);
  const char *app_id = eos_app_manager_transaction_get_application_id (transaction);

  eos_app_log_info_message ("Downloading - bundle URI: %s", bundle_uri);
  eos_app_log_info_message ("Downloading - bundle app id: %s", app_id);

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
  char *bundle_path = g_build_filename (BUNDLEDIR, bundle_name, NULL);
  g_free (bundle_name);

  eos_app_log_info_message ("Bundle save path is %s", bundle_path);

  if (!download_file_from_uri_with_retry (self, app_id,
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
get_bundle_artifacts(EosAppListModel *self,
                     const char *desktop_id,
                     char *transaction_path,
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

  if (error != NULL) {
    eos_app_log_error_message ("Getting dbus transaction failed");

    goto out;
  }

  eos_app_log_info_message ("Downloading bundle");
  bundle_path = download_bundle (self, transaction, cancellable, &error);
  if (error != NULL) {
    eos_app_log_info_message ("Download of bundle failed");

    goto out;
  }

  eos_app_log_info_message ("Downloading signature");
  signature_path = download_signature (self, transaction, cancellable, &error);
  if (error != NULL) {
    eos_app_log_error_message ("Signature download failed");

    goto out;
  }

  eos_app_log_info_message ("Downloading hash");
  sha256_path = create_sha256sum (self, transaction, bundle_path, cancellable, &error);
  if (error != NULL) {
    eos_app_log_error_message ("Hash download failed");

    goto out;
  }

  eos_app_log_info_message ("Completing transaction with eam");

  /* call this manually, since we want to specify a custom timeout */
  GVariant *res = g_dbus_proxy_call_sync (G_DBUS_PROXY (transaction),
                                          "CompleteTransaction",
                                          g_variant_new ("(s)",
                                                         bundle_path),
                                          G_DBUS_CALL_FLAGS_NONE,
                                          G_MAXINT,
                                          cancellable,
                                          &error);

  if (res != NULL)
    {
      g_variant_get (res, "(b)", &retval);
      g_variant_unref (res);
    }

out:
  if (error != NULL) {
    eos_app_log_error_message ("Completion of transaction %s failed",
                               transaction_path);

    if (transaction != NULL)
      {
        /* cancel the transaction on error */
        eos_app_manager_transaction_call_cancel_transaction_sync (transaction, NULL, NULL);
      }

    /* delete the downloaded bundle and signature */
    if (bundle_path)
      g_unlink (bundle_path);
    if (signature_path)
      g_unlink (signature_path);
    if (sha256_path)
      g_unlink (sha256_path);

    /* Bubble the error up */
    g_propagate_error (error_out, error);

    return FALSE;
  }

  /* We're done with the transaction now that we've called CompleteTransaction() */
  if (transaction != NULL)
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

static gboolean
install_latest_app_version (EosAppListModel *self,
                            const char *desktop_id,
                            const gboolean is_upgrade,
                            const gboolean allow_deltas,
                            GCancellable *cancellable,
                            GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      set_app_installation_error (desktop_id,
                                  "Could not get DBus proxy object - canceling",
                                  NULL, /* External error text */
                                  error_out);
      return FALSE;
    }

  char *app_id = app_id_from_desktop_id (desktop_id);
  char *transaction_path = NULL;

  eos_app_log_info_message ("Calling install dbus method with app_id: %s",
                            app_id);

  /* We use different DBus targets but everything else is same */
  if (is_upgrade)
    eos_app_manager_call_update_sync (proxy, app_id, allow_deltas,
                                      &transaction_path,
                                      NULL,
                                      &error);
  else
    eos_app_manager_call_install_sync (proxy, app_id,
                                       &transaction_path,
                                       NULL,
                                       &error);

  g_free (app_id);

  if (error != NULL)
    {
      /* errors coming out of DBus are generally obscure and not
       * useful for users; we log them on the session log and journal
       * but report a generic error to the UI
       */

      eos_app_log_error_message ("Got an error getting the transaction");

      g_warning ("Unable to install '%s': %s", desktop_id, error->message);

      /* the app manager may send us specific errors */
      char *message = NULL;
      if (g_dbus_error_is_remote_error (error))
        {
          char *code = g_dbus_error_get_remote_error (error);

          if (g_strcmp0 (code, "com.endlessm.AppManager.Error.NotAuthorized") == 0)
            message = _("You must be an administrator to install applications");

          g_free (code);
        }

      set_app_installation_error (desktop_id,
                                  "Installation of app failed",
                                  message,
                                  error_out);

      g_error_free (error);

      return FALSE;
    }

  if (transaction_path == NULL || *transaction_path == '\0')
    {
      set_app_installation_error (desktop_id,
                                  "Transaction path is empty - canceling",
                                  NULL, /* External message */
                                  error_out);

      return FALSE;
    }

  eos_app_log_info_message ("Got transaction path: %s", transaction_path);

  retval = get_bundle_artifacts(self, desktop_id, transaction_path, cancellable, &error);

  if (error != NULL)
    {
      eos_app_log_error_message ("Transaction %s failed", transaction_path);

      if (error->domain == EOS_APP_LIST_MODEL_ERROR)
        /* propagate only the errors we generate as they are... */
        g_propagate_error (error_out, error);
      else
        set_app_installation_error (desktop_id,
                                    error->message,
                                    NULL, /* External message */
                                    error_out);

      retval = FALSE;
    }

  g_free (transaction_path);

  return retval;
}

static gboolean
add_app_from_manager (EosAppListModel *self,
                      const char *desktop_id,
                      GCancellable *cancellable,
                      GError **error_out)
{
  eos_app_log_info_message ("Attempting to install %s", desktop_id);

  return install_latest_app_version (self,
                                     desktop_id,
                                     FALSE, /* Is update? */
                                     FALSE, /* Allow deltas (not applicable) */
                                     cancellable,
                                     error_out);
}

static gboolean
update_app_from_manager (EosAppListModel *self,
                         const char *desktop_id,
                         GCancellable *cancellable,
                         GError **error_out)
{
  gboolean retval = FALSE;

  /* First try to do an xdelta upgrade */
  eos_app_log_info_message ("Attempting to update %s using deltas", desktop_id);

  retval = install_latest_app_version (self,
                                       desktop_id,
                                       TRUE, /* Is update? */
                                       TRUE, /* Allow deltas */
                                       cancellable,
                                       error_out);

  /* Incremental update worked. Nothing else is needed */
  if (retval && error_out == NULL)
    return TRUE;

  eos_app_log_info_message ("Update of %s using deltas failed. Trying full update",
                            desktop_id);

  /* We don't care what the problem was (at this time) */
  g_clear_error (error_out);

  /* Incremental update failed so we try the full update now */
  return install_latest_app_version (self,
                                     desktop_id,
                                     TRUE, /* Is update? */
                                     FALSE, /* Allow deltas */
                                     cancellable,
                                     error_out);
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
      g_warning ("Unable to remove application '%s': %s",
                 desktop_id, error->message);
      g_error_free (error);

      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_FAILED,
                   _("Removing '%s' from the desktop failed"),
                   desktop_id);

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
  gboolean retval = FALSE;
  gchar *app_id = app_id_from_desktop_id (desktop_id);

  EosAppManager *proxy = get_eam_dbus_proxy (self);
  if (proxy == NULL)
    {
      eos_app_log_error_message ("Could not get DBus proxy object - canceling");

      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                   _("Application '%s' could not be uninstalled"),
                   desktop_id);

      return FALSE;
    }

  eos_app_log_info_message ("Trying to uninstall %s", app_id);

  eos_app_manager_call_uninstall_sync (proxy, app_id, &retval, NULL, &error);

  g_free (app_id);

  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to uninstall application '%s': %s",
                                 desktop_id, error->message);
      g_warning ("Unable to uninstall application '%s': %s",
                 desktop_id, error->message);

      /* the app manager may send us specific errors */
      char *message = NULL;
      if (g_dbus_error_is_remote_error (error))
        {
          char *code = g_dbus_error_get_remote_error (error);

          if (g_strcmp0 (code, "com.endlessm.AppManager.Error.NotAuthorized") == 0)
            message = _("You must be an administrator to remove applications");

          g_free (code);
        }

      if (message != NULL)
        {
          g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                       EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                       _("Application '%s' could not be uninstalled. %s"),
                       desktop_id,
                       message);
        }
      else
        {
          g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                       EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                       _("Application '%s' could not be uninstalled"),
                       desktop_id);
        }

      g_error_free (error);

      return FALSE;
    }

  if (!retval)
    g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                 EOS_APP_LIST_MODEL_ERROR_UNINSTALL_FAILED,
                 _("Application '%s' could not be removed"),
                 desktop_id);


  eos_app_log_info_message ("Uninstall return value from eam: %s",
                            retval ? "OK" : "Fail");

  return retval;
}

/**
 * eos_app_list_model_get_all_apps:
 * @model:
 *
 * Returns: (transfer container) (element-type utf8):
 */
GList *
eos_app_list_model_get_all_apps (EosAppListModel *model)
{
  eos_app_log_debug_message ("Retrieving all installed and available apps");

  GList *gio_apps = NULL;
  GList *apps = NULL;

  if (model->gio_apps)
    gio_apps = g_hash_table_get_keys (model->gio_apps);

  /* TODO: make sure that this only does available apps after
   * we add handlers to different update state types to model->apps
   */
  if (model->apps)
    apps = g_hash_table_get_keys (model->apps);

  return g_list_concat (gio_apps, apps);
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
    return NULL;

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
  EosAppListModelItem *item;

  if (model->apps == NULL)
    return FALSE;

  if (!g_hash_table_contains (model->apps, desktop_id))
    return FALSE;

  item = g_hash_table_lookup (model->apps, desktop_id);

  return item->state == EOS_APP_STATE_AVAILABLE;
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
  /* An app is installed if GIO knows about it */
  return (eos_app_list_model_get_app_info (model, desktop_id) != NULL);
}

static const gchar *
app_get_localized_id_for_installed_app (EosAppListModel *model,
                                        const gchar *desktop_id)
{
  GDesktopAppInfo *info;
  char *localized_id;

  info = g_hash_table_lookup (model->gio_apps, desktop_id);
  if (info)
    goto out;

  localized_id = localized_id_from_desktop_id (desktop_id);
  info = g_hash_table_lookup (model->gio_apps, localized_id);
  g_free (localized_id);

 out:
  if (info)
    return g_app_info_get_id (G_APP_INFO (info));
  else
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
  gboolean is_installed, is_updatable = FALSE;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), EOS_APP_STATE_UNKNOWN);
  g_return_val_if_fail (desktop_id != NULL, EOS_APP_STATE_UNKNOWN);

  is_installed = app_is_installed (model, desktop_id);
  if (is_installed)
    {
      const char *localized_id;
      localized_id = app_get_localized_id_for_installed_app (model, desktop_id);
      is_updatable = app_is_updatable (model, localized_id);
    }

  if (is_installed && is_updatable)
    retval = EOS_APP_STATE_UPDATABLE;
  else if (is_installed)
    retval = EOS_APP_STATE_INSTALLED;
  else
    retval = EOS_APP_STATE_AVAILABLE;

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

  if (!app_is_installed (model, desktop_id))
    {
      if (!desktop_id_is_web_link (desktop_id) &&
          model->can_install &&
          !add_app_from_manager (model, desktop_id, cancellable, &error))
        {
          g_task_return_error (task, error);
          return;
        }
     }

  if (!add_app_to_shell (model, desktop_id, cancellable, &error))
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
                               EOS_APP_LIST_MODEL_ERROR_FAILED,
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
                               EOS_APP_LIST_MODEL_ERROR_FAILED,
                               _("App %s not installable"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  if (!app_is_updatable (model, localized_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NO_UPDATE_AVAILABLE,
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
  const gchar *desktop_id = task_data;

  if (model->can_uninstall && !remove_app_from_manager (model, desktop_id, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  if (!remove_app_from_shell (model, desktop_id, cancellable, &error))
    {
      g_task_return_error (task, error);
      return;
    }

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
  return g_task_propagate_boolean (G_TASK (result), error);
}

gboolean
eos_app_list_model_launch_app (EosAppListModel *model,
                               const char *desktop_id,
                               guint32 timestamp,
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

  return launch_app (model, localized_id, timestamp, NULL, error);
}

gboolean
eos_app_list_model_has_app (EosAppListModel *model,
                            const char *desktop_id)
{
  gchar *localized_id;
  gboolean res;

  if (eos_app_list_model_get_app_info (model, desktop_id) != NULL)
    return TRUE;

  if (app_is_installable (model, desktop_id))
    return TRUE;

  localized_id = localized_id_from_desktop_id (desktop_id);
  res = app_is_installable (model, localized_id);
  g_free (localized_id);

  return res;
}

gboolean
eos_app_list_model_get_app_can_remove (EosAppListModel *model,
                                       const char *desktop_id)
{
  const gchar *localized_id;

  if (model->manager_installed_apps == NULL)
    return FALSE;

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);

  /* Can only remove what the manager installed... */
  if (!g_hash_table_contains (model->manager_installed_apps, localized_id))
    return FALSE;

  /* ... and what the manager tells us it's removable */
  if (!g_hash_table_contains (model->manager_removable_apps, localized_id))
    return FALSE;

  return TRUE;
}
