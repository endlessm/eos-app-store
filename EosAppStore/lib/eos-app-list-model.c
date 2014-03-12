/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-list-model.h"

#include <glib-object.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <glib/gi18n-lib.h>

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gmenu-tree.h>

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *connection;

  GMenuTree *app_tree;

  GHashTable *apps_by_id;
  GHashTable *installed_apps;

  guint applications_changed_id;
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

static GHashTable *
load_installed_apps_from_gvariant (GVariant *apps)
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

static void
on_app_tree_changed (GMenuTree       *tree,
                     EosAppListModel *self)
{
  if (self->apps_by_id != NULL)
    {
      g_hash_table_unref (self->apps_by_id);
      self->apps_by_id = NULL;
    }

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

  if (self->installed_apps != NULL)
    {
      g_hash_table_unref (self->installed_apps);
      self->installed_apps = NULL;
    }

  self->installed_apps = load_installed_apps_from_gvariant (parameters);

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  if (self->applications_changed_id != 0)
    {
      g_dbus_connection_signal_unsubscribe (self->connection,
                                            self->applications_changed_id);
      self->applications_changed_id = 0;
    }

  g_clear_object (&self->connection);
  g_clear_object (&self->app_tree);
  g_hash_table_unref (self->apps_by_id);
  g_hash_table_unref (self->installed_apps);

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
  self->connection = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);

  self->app_tree =
    gmenu_tree_new ("gnome-applications.menu", GMENU_TREE_FLAGS_INCLUDE_NODISPLAY);
  g_signal_connect (self->app_tree, "changed",
                    G_CALLBACK (on_app_tree_changed),
                    self);

  self->applications_changed_id =
    g_dbus_connection_signal_subscribe (self->connection,
                                        "org.gnome.Shell",
                                        "org.gnome.Shell.AppStore",
                                        "ApplicationsChanged",
                                        "/org/gnome/Shell",
                                        NULL, G_DBUS_SIGNAL_FLAGS_NONE,
                                        on_shell_applications_changed,
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

  res = g_dbus_connection_call_sync (self->connection,
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
      g_critical ("Unable to add application '%s': %s",
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

  g_dbus_connection_call_sync (self->connection,
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
      g_critical ("Unable to add application '%s': %s",
                  desktop_id,
                  error->message);
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

  g_dbus_connection_call_sync (self->connection,
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
      g_critical ("Unable to remove application '%s': %s",
                  desktop_id,
                  error->message);
      g_propagate_error (error_out, error);

      return FALSE;
    }

  return TRUE;
}

static GHashTable *
load_installed_apps (EosAppListModel *self)
{
  GVariant *applications;
  GError *error = NULL;
  GHashTable *retval;

  applications =
    g_dbus_connection_call_sync (self->connection,
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

      return NULL;
    }

  retval = load_installed_apps_from_gvariant (applications);
  g_variant_unref (applications);

  return retval;
}

static void
flatten_menu_tree_recursive (gpointer    directory,
                             GHashTable *set)
{
  GMenuTreeIter *iter = gmenu_tree_directory_iter (directory);
  GMenuTreeItemType item_type;
  gpointer item;

  item_type = gmenu_tree_iter_next (iter);
  while (item_type != GMENU_TREE_ITEM_INVALID)
    {
      switch (item_type)
        {
        case GMENU_TREE_ITEM_ENTRY:
          {
            const char *file_id;

            item = gmenu_tree_iter_get_entry (iter);
            file_id = gmenu_tree_entry_get_desktop_file_id (item);
            g_hash_table_replace (set, (gpointer) file_id, item);
          }
          break;

        case GMENU_TREE_ITEM_DIRECTORY:
          item = gmenu_tree_iter_get_directory (iter);
          flatten_menu_tree_recursive (item, set);
          gmenu_tree_item_unref (item);
          break;

        default:
          break;
        }

      item_type = gmenu_tree_iter_next (iter);
    }

  gmenu_tree_iter_unref (iter);
}

static void
tree_load_in_thread (GTask        *task,
                     gpointer      object,
                     gpointer      task_data,
                     GCancellable *cancellable)
{
  EosAppListModel *model = object;
  GMenuTreeDirectory *root;
  GError *error = NULL;
  GHashTable *set;

  if (model->apps_by_id != NULL)
    {
      g_hash_table_unref (model->apps_by_id);
      model->apps_by_id = NULL;
    }

  if (!gmenu_tree_load_sync (model->app_tree, &error))
    {
      g_task_return_error (task, error);
      return;
    }

  set = g_hash_table_new_full (g_str_hash, g_str_equal,
                               NULL,
                               gmenu_tree_item_unref);

  root = gmenu_tree_get_root_directory (model->app_tree);
  if (root == NULL)
    {
      g_task_return_pointer (task, NULL, NULL);
      return;
    }

  flatten_menu_tree_recursive (root, set);

  gmenu_tree_item_unref (root);

  model->apps_by_id = set;
  model->installed_apps = load_installed_apps (model);

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
  g_task_run_in_thread (task, tree_load_in_thread);
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
  g_return_val_if_fail (g_task_is_valid (result, model), NULL);

  if (model->apps_by_id == NULL || g_task_had_error (G_TASK (result)))
    return g_task_propagate_pointer (G_TASK (result), error);

  return g_hash_table_get_keys (model->apps_by_id);
}

static gboolean
is_app_installed (EosAppListModel *model,
                  const char      *desktop_id)
{
  if (model->installed_apps == NULL)
    return FALSE;

  return g_hash_table_contains (model->installed_apps, desktop_id);
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
GDesktopAppInfo *
eos_app_list_model_get_app_info (EosAppListModel *model,
                                 const char *desktop_id)
{
  GMenuTreeEntry *entry;
  GDesktopAppInfo *res;

  if (model->apps_by_id == NULL)
    {
      g_critical ("The application list is not loaded.");
      return NULL;
    }

  entry = g_hash_table_lookup (model->apps_by_id, desktop_id);

  if (entry == NULL)
    {
      g_critical ("No application '%s' was found.", desktop_id);
      return NULL;
    }

  res = gmenu_tree_entry_get_app_info (entry);

  return res;
}

const char *
eos_app_list_model_get_app_name (EosAppListModel *model,
                                 const char *desktop_id)
{
  GDesktopAppInfo *info;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (desktop_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_NAME);
}

const char *
eos_app_list_model_get_app_executable (EosAppListModel *model,
                                       const char *desktop_id)
{
  GDesktopAppInfo *info;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (desktop_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_EXEC);
}

const char *
eos_app_list_model_get_app_description (EosAppListModel *model,
                                        const char *desktop_id)
{
  return NULL;
}

const char *
eos_app_list_model_get_app_comment (EosAppListModel *model,
                                    const char *desktop_id)
{
  GDesktopAppInfo *info;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (desktop_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_COMMENT);
}

const char *
eos_app_list_model_get_app_icon_name (EosAppListModel *model,
                                      const char *desktop_id,
                                      EosAppIconState icon_state)
{
  GDesktopAppInfo *info;
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (desktop_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_ICON);
}

EosAppState
eos_app_list_model_get_app_state (EosAppListModel *model,
                                  const char *desktop_id)
{
  EosAppState retval = EOS_APP_STATE_UNKNOWN;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), EOS_APP_STATE_UNKNOWN);
  g_return_val_if_fail (desktop_id != NULL, EOS_APP_STATE_UNKNOWN);

  if (is_app_installed (model, desktop_id))
    {
      retval = EOS_APP_STATE_INSTALLED;
      goto out;
    }

  if (eos_app_list_model_get_app_info (model, desktop_id) != NULL)
    {
      retval = EOS_APP_STATE_UNINSTALLED;
      goto out;
    }

 out:
  return retval;
}

gboolean
eos_app_list_model_get_app_visible (EosAppListModel *model,
                                    const char *desktop_id)
{
  GDesktopAppInfo *info;
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), FALSE);
  g_return_val_if_fail (desktop_id != NULL, FALSE);

  info = eos_app_list_model_get_app_info (model, desktop_id);
  if (info == NULL)
    return FALSE;

  return !(g_desktop_app_info_get_nodisplay (info) ||
           g_desktop_app_info_get_is_hidden (info));
}

void
eos_app_list_model_install_app (EosAppListModel *model,
                                const char *desktop_id)
{
  if (is_app_installed (model, desktop_id))
    return;

  if (!add_app_to_shell (model, desktop_id, NULL, NULL))
    return;

  g_hash_table_add (model->installed_apps, g_strdup (desktop_id));
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

  if (!add_app_to_shell (model, desktop_id, cancellable, &error))
    g_task_return_error (task, error);
  else
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

  task = g_task_new (model, cancellable, callback, user_data);
  g_task_set_task_data (task, g_strdup (desktop_id), (GDestroyNotify) g_free);

  if (is_app_installed (model, desktop_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_INSTALLED,
                               _("Application %s already installed"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_run_in_thread (task, add_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_install_app_finish (EosAppListModel *model,
                                       GAsyncResult *result,
                                       GError **error)
{
  GTask *task = G_TASK (result);
  const gchar *desktop_id;

  if (!g_task_propagate_boolean (task, error))
    return FALSE;

  desktop_id = g_task_get_task_data (task);
  g_hash_table_add (model->installed_apps, g_strdup (desktop_id));
  return TRUE;
}

void
eos_app_list_model_update_app (EosAppListModel *model,
                               const char *desktop_id)
{
}

void
eos_app_list_model_uninstall_app (EosAppListModel *model,
                                  const char *desktop_id)
{
  if (!is_app_installed (model, desktop_id))
    return;

  if (!remove_app_from_shell (model, desktop_id, NULL, NULL))
    return;

  g_hash_table_remove (model->installed_apps, desktop_id);
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

  if (!remove_app_from_shell (model, desktop_id, cancellable, &error))
    g_task_return_error (task, error);
  else
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

  task = g_task_new (model, cancellable, callback, user_data);
  g_task_set_task_data (task, g_strdup (desktop_id), (GDestroyNotify) g_free);

  if (!is_app_installed (model, desktop_id))
    {
      g_task_return_new_error (task,
                               eos_app_list_model_error_quark (),
                               EOS_APP_LIST_MODEL_ERROR_NOT_INSTALLED,
                               _("Application %s is not installed"),
                               desktop_id);
      g_object_unref (task);
      return;
    }

  g_task_run_in_thread (task, remove_app_thread_func);
  g_object_unref (task);
}

gboolean
eos_app_list_model_uninstall_app_finish (EosAppListModel *model,
                                         GAsyncResult *result,
                                         GError **error)
{
  GTask *task = G_TASK (result);
  const gchar *desktop_id;

  if (!g_task_propagate_boolean (task, error))
    return FALSE;

  desktop_id = g_task_get_task_data (task);
  g_hash_table_remove (model->installed_apps, desktop_id);
  return TRUE;
}

gboolean
eos_app_list_model_launch_app (EosAppListModel *model,
                               const char *desktop_id)
{
  if (!is_app_installed (model, desktop_id))
    return FALSE;

  return launch_app (model, desktop_id, NULL, NULL);
}
