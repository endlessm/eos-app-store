/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-list-model.h"
#include "eos-app-manager-transaction.h"

#include <glib-object.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <glib/gi18n-lib.h>
#include <libsoup/soup.h>

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *system_bus;
  GDBusConnection *session_bus;

  GAppInfoMonitor *app_monitor;

  GHashTable *gio_apps;
  GHashTable *shell_apps;
  GHashTable *installable_apps;
  GHashTable *updatable_apps;
  GHashTable *manager_installed_apps;

  GCancellable *load_cancellable;

  guint applications_changed_id;
  guint available_apps_changed_id;

  gboolean can_install;
  gboolean can_uninstall;

  SoupSession *soup_session;
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

G_DEFINE_TYPE (EosAppListModel, eos_app_list_model, G_TYPE_OBJECT)
G_DEFINE_QUARK (eos-app-list-model-error-quark, eos_app_list_model_error)

#define WEB_LINK_ID_PREFIX "eos-link-"

static void load_manager_installed_apps (EosAppListModel *self);

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
on_app_monitor_changed (GAppInfoMonitor *monitor,
                        EosAppListModel *self)
{
  g_clear_pointer (&self->gio_apps, g_hash_table_unref);
  self->gio_apps = load_apps_from_gio ();

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);

  /* queue a reload of the manager-installed apps */
  load_manager_installed_apps (self);
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

  g_clear_pointer (&self->installable_apps, g_hash_table_unref);
  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  GVariantIter *iter1, *iter2;

  g_variant_get (parameters, "(a(sss)a(sss))", &iter1, &iter2);

  self->installable_apps = load_installable_apps_from_gvariant (iter1);
  self->updatable_apps = load_installable_apps_from_gvariant (iter2);

  g_variant_iter_free (iter1);
  g_variant_iter_free (iter2);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

typedef struct {
  GHashTable *installable_apps;
  GHashTable *updatable_apps;
} AllAppsData;

static void
all_apps_data_free (AllAppsData *data)
{
  g_clear_pointer (&data->installable_apps, g_hash_table_unref);
  g_clear_pointer (&data->updatable_apps, g_hash_table_unref);

  g_slice_free (AllAppsData, data);
}

static void
on_app_manager_apps_loaded (GObject *source,
                            GAsyncResult *result,
                            gpointer user_data)
{
  GTask *task = G_TASK (result);
  EosAppListModel *self = EOS_APP_LIST_MODEL (source);
  AllAppsData *data;

  g_clear_object (&self->load_cancellable);

  if (g_task_had_error (task))
    {
      g_critical ("The application list model could not be loaded because of an error");
      return;
    }

  data = g_task_propagate_pointer (task, NULL);
  g_assert (data != NULL);

  g_clear_pointer (&self->installable_apps, g_hash_table_unref);
  g_clear_pointer (&self->updatable_apps, g_hash_table_unref);

  self->installable_apps = g_hash_table_ref (data->installable_apps);
  self->updatable_apps = g_hash_table_ref (data->updatable_apps);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static gboolean
load_available_apps (EosAppListModel *self,
                     GHashTable **installable_apps_out,
                     GHashTable **updatable_apps_out,
                     GCancellable *cancellable,
                     GError **error_out)
{
  GVariant *applications;
  GError *error = NULL;

  const char * const *locales = g_get_language_names ();
  const char *locale_name = locales[0];

  char **variants = g_get_locale_variants (locale_name);
  const char *lang_id = variants[g_strv_length (variants) - 1];

  GVariantBuilder builder;

  g_variant_builder_init (&builder, G_VARIANT_TYPE ("(a{sv})"));
  g_variant_builder_open (&builder, G_VARIANT_TYPE ("a{sv}"));
  g_variant_builder_add (&builder, "{sv}", "Locale", g_variant_new_string (lang_id));
  g_variant_builder_close (&builder);

  g_strfreev (variants);

  applications =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager",
                                 "ListAvailable",
                                 g_variant_builder_end (&builder), NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 cancellable,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list available applications: %s",
                  error->message);
      g_propagate_error (error_out, error);
      return FALSE;
    }

  GVariantIter *iter1, *iter2;

  g_variant_get (applications, "(a(sss)a(sss))", &iter1, &iter2);

  if (installable_apps_out != NULL)
    *installable_apps_out = load_installable_apps_from_gvariant (iter1);
  if (updatable_apps_out != NULL)
    *updatable_apps_out = load_installable_apps_from_gvariant (iter2);

  g_variant_iter_free (iter1);
  g_variant_iter_free (iter2);
  g_variant_unref (applications);

  return TRUE;
}

static gboolean
load_user_capabilities (EosAppListModel *self,
                        GCancellable *cancellable,
                        GError **error_out)
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
                                 cancellable,
                                 &error);

  if (error != NULL)
    {
      g_critical ("Unable to list retrieve user capabilities: %s",
                  error->message);
      g_propagate_error (error_out, error);
      return FALSE;
    }


  GVariant *caps;
  caps = g_variant_get_child_value (capabilities, 0);

  g_variant_lookup (caps, "CanInstall", "b", &self->can_install);
  g_variant_lookup (caps, "CanUninstall", "b", &self->can_uninstall);

  g_variant_unref (caps);
  g_variant_unref (capabilities);

  return TRUE;
}

static void
app_manager_apps_load_in_thread (GTask        *task,
                                 gpointer      object,
                                 gpointer      task_data,
                                 GCancellable *cancellable)
{
  EosAppListModel *model = object;
  GError *error = NULL;
  AllAppsData *data;

  data = g_slice_new0 (AllAppsData);

  if (!load_available_apps (model, &data->installable_apps, &data->updatable_apps,
                            cancellable, &error))
    goto out;

  if (!load_user_capabilities (model, cancellable, &error))
    goto out;

 out:
  if (error != NULL)
    {
      all_apps_data_free (data);
      g_task_return_error (task, error);
    }
  else
    {
      g_task_return_pointer (task, data, (GDestroyNotify) all_apps_data_free);
    }
}

static void
on_manager_installed_apps_loaded (GObject *source,
                                  GAsyncResult *result,
                                  gpointer user_data)
{
  EosAppListModel *self = user_data;
  GVariant *applications;
  GError *error = NULL;

  applications = g_dbus_connection_call_finish (G_DBUS_CONNECTION (source),
                                                result, &error);

  if (error != NULL)
    {
      g_critical ("Unable to load manager installed applications: %s",
                  error->message);
      g_error_free (error);
      return;
    }

  GVariantIter *iter;

  g_variant_get (applications, "(a(sss))", &iter);

  g_clear_pointer (&self->manager_installed_apps, g_hash_table_unref);
  self->manager_installed_apps = load_installable_apps_from_gvariant (iter);

  g_variant_iter_free (iter);
  g_variant_unref (applications);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
load_manager_installed_apps (EosAppListModel *self)
{
  g_dbus_connection_call (self->system_bus,
                          "com.endlessm.AppManager",
                          "/com/endlessm/AppManager",
                          "com.endlessm.AppManager",
                          "ListInstalled",
                          NULL, NULL,
                          G_DBUS_CALL_FLAGS_NONE,
                          -1,
                          self->load_cancellable,
                          on_manager_installed_apps_loaded,
                          self);
}

static void
load_shell_apps (EosAppListModel *self)
{
  GVariant *applications;
  GError *error = NULL;

  applications =
    g_dbus_connection_call_sync (self->session_bus,
                                 "org.gnome.Shell",
                                 "/org/gnome/Shell",
                                 "org.gnome.Shell.AppStore",
                                 "ListApplications",
                                 NULL, NULL,
                                 G_DBUS_CALL_FLAGS_NONE,
                                 -1,
                                 self->load_cancellable,
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

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
load_all_apps (EosAppListModel *self)
{
  GTask *task;

  /* Load GIO apps */
  self->gio_apps = load_apps_from_gio ();

  /* Load app manager apps in a thread */
  self->load_cancellable = g_cancellable_new ();
  task = g_task_new (self, self->load_cancellable, on_app_manager_apps_loaded, NULL);
  g_task_run_in_thread (task, app_manager_apps_load_in_thread);
  g_object_unref (task);

  /* Load shell apps */
  load_shell_apps (self);

  /* Load manager-installed apps */
  load_manager_installed_apps (self);
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

  g_clear_object (&self->soup_session);
  g_clear_object (&self->app_monitor);
  g_clear_object (&self->session_bus);
  g_clear_object (&self->system_bus);

  g_hash_table_unref (self->gio_apps);
  g_hash_table_unref (self->shell_apps);
  g_hash_table_unref (self->updatable_apps);
  g_hash_table_unref (self->installable_apps);
  g_hash_table_unref (self->manager_installed_apps);

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

  load_all_apps (self);
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

typedef struct {
  EosAppListModel *model;
  char *app_id;
  goffset current;
  goffset total;
} ProgressClosure;

static void
progress_closure_free (gpointer _data)
{
  ProgressClosure *data = _data;

  g_clear_object (&data->model);
  g_free (data->app_id);

  g_slice_free (ProgressClosure, data);
}

static gboolean
emit_download_progress (gpointer _data)
{
  ProgressClosure *data = _data;

  g_signal_emit (data->model, eos_app_list_model_signals[DOWNLOAD_PROGRESS], 0,
                 data->app_id,
                 data->current,
                 data->total);

  return G_SOURCE_REMOVE;
}

static void
queue_download_progress (EosAppListModel *self,
                         const char      *app_id,
                         goffset          current,
                         goffset          total)
{
  ProgressClosure *clos = g_slice_new (ProgressClosure);

  clos->model = g_object_ref (self);
  clos->app_id = g_strdup (app_id);
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

  info = g_file_query_filesystem_info (path, G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                       cancellable,
                                       error);
  if (info == NULL)
    return FALSE;

  guint64 free_space = g_file_info_get_attribute_uint64 (info, G_FILE_ATTRIBUTE_FILESYSTEM_FREE);
  guint64 req_space = min_size * 2;

  if (free_space < req_space)
    {
      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Not enough space on device for downloading app"));
      retval = FALSE;
    }

  g_object_unref (info);

  return retval;
}

static gboolean
download_bundle_from_uri (EosAppListModel *self,
                          const char      *app_id,
                          const char      *source_uri,
                          char           **target_file,
                          GCancellable    *cancellable,
                          GError         **error)
{
  GError *internal_error = NULL;
  gboolean retval = FALSE;

  SoupURI *uri = soup_uri_new (source_uri);

  if (uri == NULL)
    {
      g_set_error (error, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Invalid URI for the app '%s' bundle: %s"),
                   app_id,
                   source_uri);
      return FALSE;
    }

  if (self->soup_session == NULL)
    self->soup_session = soup_session_async_new ();

  SoupRequest *request = soup_session_request_uri (self->soup_session, uri, &internal_error);

  soup_uri_free (uri);

  if (internal_error != NULL)
    {
      g_propagate_error (error, internal_error);
      return FALSE;
    }

  GByteArray *content = NULL;
  GFileOutputStream *out_stream = NULL;
  GInputStream *in_stream = soup_request_send (request, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      g_propagate_error (error, internal_error);
      g_object_unref (request);
      return FALSE;
    }

  goffset total = soup_request_get_content_length (request);

  char *bundle_file = g_strconcat (app_id, ".bundle", NULL);
  char *target = g_build_filename (g_get_tmp_dir (), "eos-app-store", bundle_file, NULL);
  g_free (bundle_file);

  GFile *file = g_file_new_for_path (target);
  GFile *parent = g_file_get_parent (file);

  g_file_make_directory_with_parents (parent, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      g_propagate_error (error, internal_error);
      retval = FALSE;
      goto out;
    }

  if (!check_available_space (parent, total, cancellable, &internal_error))
    {
      g_propagate_error (error, internal_error);
      retval = FALSE;
      goto out;
    }

  out_stream = g_file_create (file, G_FILE_CREATE_NONE, cancellable, &internal_error);
  if (internal_error != NULL)
    {
      g_propagate_error (error, internal_error);
      retval = FALSE;
      goto out;
    }

#define GET_DATA_BLOCK_SIZE     64 * 1024

  /* ensure we emit a progress notification at the beginning */
  queue_download_progress (self, app_id, 0, total);

  gssize res = 0;
  gsize pos = 0;
  content = g_byte_array_new ();
  g_byte_array_set_size (content, GET_DATA_BLOCK_SIZE);

  /* we don't use splice() because it does not have progress, and the
   * data is coming from a network request, so it won't have a file
   * descriptor we can use splice() on
   */
  while ((res = g_input_stream_read (in_stream, content->data,
                                     GET_DATA_BLOCK_SIZE,
                                     cancellable, &internal_error)) > 0)
    {
      g_output_stream_write (G_OUTPUT_STREAM (out_stream), content->data, res,
                             cancellable,
                             &internal_error);
      if (internal_error != NULL)
        {
          g_propagate_error (error, internal_error);
          retval = FALSE;
          goto out;
        }

      pos += res;

      queue_download_progress (self, app_id, pos, total);
    }

  if (res < 0)
    {
      g_propagate_error (error, internal_error);
      retval = FALSE;
      goto out;
    }

  /* ensure we emit a progress notification for the whole size */
  queue_download_progress (self, app_id, total, total);

  if (target_file != NULL)
    *target_file = g_strdup (target);

  retval = TRUE;

out:
  g_clear_pointer (&content, g_byte_array_unref);
  g_clear_object (&file);
  g_clear_object (&parent);
  g_clear_object (&in_stream);
  g_clear_object (&out_stream);
  g_clear_object (&request);
  g_free (target);

#undef GET_DATA_BLOCK_SIZE

  return retval;
}

static gboolean
add_app_from_manager (EosAppListModel *self,
                      const char *desktop_id,
                      GCancellable *cancellable,
                      GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;
  char *app_id = app_id_from_desktop_id (desktop_id);
  char *transaction_path = NULL;
  GVariant *res =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager", "Install",
                                 g_variant_new ("(s)", app_id),
                                 G_VARIANT_TYPE ("(o)"),
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

  if (res != NULL)
    {
      g_variant_get (res, "(o)", &transaction_path);
      g_variant_unref (res);
    }

  if (transaction_path == NULL || *transaction_path == '\0')
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Application '%s' could not be installed"),
                   desktop_id);

      return FALSE;
    }

  EosAppManagerTransaction *transaction =
    eos_app_manager_transaction_proxy_new_sync (self->system_bus,
                                                G_DBUS_PROXY_FLAGS_NONE,
                                                "com.endlessm.AppManager",
                                                transaction_path,
                                                cancellable,
                                                &error);
  if (error != NULL)
    {
      g_free (transaction_path);
      g_propagate_error (error_out, error);
      return FALSE;
    }

  const char *bundle_uri = eos_app_manager_transaction_get_bundle_uri (transaction);

  if (bundle_uri == NULL || *bundle_uri == '\0')
    {
      g_free (transaction_path);
      g_object_unref (transaction);
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Application '%s' could not be installed"),
                   desktop_id);
      return FALSE;
    }

  char *bundle_path = NULL;

  if (!download_bundle_from_uri (self, desktop_id, bundle_uri, &bundle_path, cancellable, &error))
    {
      g_object_unref (transaction);
      g_free (transaction_path);
      g_propagate_error (error_out, error);
      return FALSE;
    }

  eos_app_manager_transaction_call_complete_transaction_sync (transaction, bundle_path,
                                                              &retval,
                                                              cancellable,
                                                              &error);

  g_object_unref (transaction);
  g_free (transaction_path);
  g_free (bundle_path);

  if (error != NULL)
    {
      g_propagate_error (error_out, error);
      return FALSE;
    }

  return retval;
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
  gboolean retval = FALSE;
  char *app_id = app_id_from_desktop_id (desktop_id);
  GVariant *res =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager", "Uninstall",
                                 g_variant_new ("(s)", app_id),
                                 G_VARIANT_TYPE ("(b)"),
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

  if (res != NULL)
    {
      g_variant_get (res, "(b)", &retval);
      g_variant_unref (res);
    }

  if (!retval)
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Application '%s' could not be removed"),
                   desktop_id);

      return FALSE;
    }

  return retval;
}

static gboolean
update_app_from_manager (EosAppListModel *self,
                         const char *desktop_id,
                         GCancellable *cancellable,
                         GError **error_out)
{
  GError *error = NULL;
  gboolean retval = FALSE;
  char *app_id = app_id_from_desktop_id (desktop_id);
  GVariant *res =
    g_dbus_connection_call_sync (self->system_bus,
                                 "com.endlessm.AppManager",
                                 "/com/endlessm/AppManager",
                                 "com.endlessm.AppManager", "Install",
                                 g_variant_new ("(s)", app_id),
                                 G_VARIANT_TYPE ("(b)"),
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

  if (res != NULL)
    {
      g_variant_get (res, "(b)", &retval);
      g_variant_unref (res);
    }

  if (!retval)
    {
      g_set_error (error_out, EOS_APP_LIST_MODEL_ERROR,
                   EOS_APP_LIST_MODEL_ERROR_NO_UPDATE,
                   _("Application '%s' could not be updated"),
                   desktop_id);

      return FALSE;
    }

  return TRUE;
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
  GList *gio_apps = NULL;
  GList *installable_apps = NULL;

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

  g_assert (model->gio_apps != NULL);

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

  if (!app_has_launcher (model, desktop_id))
    {
      if (!add_app_to_shell (model, desktop_id, cancellable, &error))
        {
          g_task_return_error (task, error);
          return;
        }
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

  localized_id = app_get_localized_id_for_installed_app (model, desktop_id);

  /* Can only remove what the manager installed */
  return g_hash_table_contains (model->manager_installed_apps, localized_id);
}
