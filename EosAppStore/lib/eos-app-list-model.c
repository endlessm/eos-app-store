#include "config.h"

#include "eos-app-list-model.h"

#include <glib-object.h>
#include <gio/gio.h>
#include <json-glib/json-glib.h>

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gmenu-tree.h>

struct _EosAppListModel
{
  GObject parent_instance;

  GDBusConnection *connection;

  GSettings *settings;

  GFileMonitor *monitor;

  GMenuTree *app_tree;

  GHashTable *apps_by_id;
  GHashTable *installed_apps;
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
on_installed_apps_changed (GFileMonitor      *monitor,
                           GFile             *file,
                           GFile             *other_file,
                           GFileMonitorEvent  event_type,
                           EosAppListModel   *self)
{
  if (self->installed_apps != NULL)
    {
      g_hash_table_unref (self->installed_apps);
      self->installed_apps = NULL;
    }

  g_signal_emit (self, eos_app_list_model_signals[CHANGED], 0);
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  g_clear_object (&self->monitor);
  g_clear_object (&self->settings);
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

static char *
get_installed_apps_path (void)
{
  return g_build_filename (g_get_home_dir (),
                           ".endlessm",
                           "installed_applications.json",
                           NULL);
}

static void
eos_app_list_model_init (EosAppListModel *self)
{
  char *installed_apps;
  GFile *file;

  self->settings = g_settings_new ("org.gnome.shell");

  self->connection = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);

  self->app_tree =
    gmenu_tree_new ("gnome-applications.menu", GMENU_TREE_FLAGS_INCLUDE_NODISPLAY);
  g_signal_connect (self->app_tree, "changed",
                    G_CALLBACK (on_app_tree_changed),
                    self);

  installed_apps = get_installed_apps_path ();
  file = g_file_new_for_path (installed_apps);
  self->monitor = g_file_monitor_file (file, G_FILE_MONITOR_SEND_MOVED, NULL, NULL);
  g_signal_connect (self->monitor, "changed",
                    G_CALLBACK (on_installed_apps_changed),
                    self);
  g_object_unref (file);
  g_free (installed_apps);
}

EosAppListModel *
eos_app_list_model_new (void)
{
  return g_object_new (EOS_TYPE_APP_LIST_MODEL, NULL);
}

static gboolean
add_app_to_shell (EosAppListModel *self,
                  const char *app_id)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->connection,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "AddApplication",
                               g_variant_new ("(s)", app_id),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               -1,
                               NULL,
                               &error);
  if (error != NULL)
    {
      g_critical ("Unable to add application '%s': %s",
                  app_id,
                  error->message);
      g_error_free (error);

      return FALSE;
    }

  return TRUE;
}

static gboolean
remove_app_from_shell (EosAppListModel *self,
                       const char *app_id)
{
  GError *error = NULL;

  g_dbus_connection_call_sync (self->connection,
                               "org.gnome.Shell",
                               "/org/gnome/Shell",
                               "org.gnome.Shell.AppStore", "RemoveApplication",
                               g_variant_new ("(s)", app_id),
                               NULL,
                               G_DBUS_CALL_FLAGS_NONE,
                               -1,
                               NULL,
                               &error);
  if (error != NULL)
    {
      g_critical ("Unable to add application '%s': %s",
                  app_id,
                  error->message);
      g_error_free (error);

      return FALSE;
    }

  return TRUE;
}

static void
add_to_set (JsonArray *array,
            guint      index_,
            JsonNode  *element,
            gpointer   data)
{
  GHashTable *set = data;

  if (JSON_NODE_HOLDS_VALUE (element) &&
      json_node_get_string (element) != NULL)
    {
      g_hash_table_add (set, json_node_dup_string (element));
    }
}

static void
save_installed_apps (EosAppListModel *self)
{
  JsonGenerator *gen;
  JsonNode *node;
  JsonArray *array;
  GHashTableIter iter;
  gpointer key;
  char *path;
  GError *error = NULL;

  path = get_installed_apps_path ();

  array = json_array_sized_new (g_hash_table_size (self->installed_apps));
  g_hash_table_iter_init (&iter, self->installed_apps);
  while (g_hash_table_iter_next (&iter, &key, NULL))
    json_array_add_string_element (array, key);

  node = json_node_init_array (json_node_alloc (), array);
  json_array_unref (array);

  gen = json_generator_new ();
  json_generator_set_root (gen, node);
  json_generator_to_file (gen, path, &error);
  if (error != NULL)
    {
      g_critical (G_STRLOC ": Unable to save installed_applications.json: %s",
                  error->message);
      g_error_free (error);
    }

  json_node_free (node);
  g_object_unref (gen);
  g_free (path);
}

static GHashTable *
load_installed_apps (void)
{
  JsonParser *parser;
  GError *internal_error;
  GHashTable *retval;
  JsonNode *root;
  char *file;

  retval = g_hash_table_new_full (g_str_hash, g_str_equal,
                                  g_free,
                                  NULL);

  file = g_build_filename (g_get_home_dir (),
                           ".endlessm",
                           "installed_applications.json",
                           NULL);

  parser = json_parser_new ();

  internal_error = NULL;
  json_parser_load_from_file (parser, file, &internal_error);
  if (internal_error != NULL)
    {
      if (!(internal_error->domain == G_FILE_ERROR &&
            internal_error->code == G_FILE_ERROR_NOENT))
        {
          g_critical (G_STRLOC ": Unable to load installed_applications.json: %s",
                      internal_error->message);
        }

      g_error_free (internal_error);
      goto out;
    }

  root = json_parser_get_root (parser);
  if (JSON_NODE_HOLDS_ARRAY (root))
    {
      JsonArray *array = json_node_get_array (root);

      json_array_foreach_element (array, add_to_set, retval);
    }

out:
  g_object_unref (parser);
  g_free (file);

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
  GList *app_list;

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
  model->installed_apps = load_installed_apps ();

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
                  const char *app_id)
{
  return g_hash_table_lookup (model->installed_apps, app_id) != NULL;
}

static GDesktopAppInfo *
eos_app_list_model_get_app_info (EosAppListModel *model,
                                 const char *app_id)
{
  GMenuTreeEntry *entry;
  GDesktopAppInfo *res;
  gchar *desktop_app_id;

  if (model->apps_by_id == NULL)
    {
      g_critical ("The application list is not loaded.");
      return NULL;
    }

  if (!g_str_has_suffix (app_id, ".desktop"))
    desktop_app_id = g_strconcat (app_id, ".desktop", NULL);
  else
    desktop_app_id = g_strdup (app_id);

  entry = g_hash_table_lookup (model->apps_by_id, desktop_app_id);
  g_free (desktop_app_id);

  if (entry == NULL)
    {
      g_critical ("No application '%s' was found.", app_id);
      return NULL;
    }

  res = gmenu_tree_entry_get_app_info (entry);

  return res;
}

const char *
eos_app_list_model_get_app_name (EosAppListModel *model,
                                 const char *app_id)
{
  GDesktopAppInfo *info;

  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (app_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, app_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_NAME);
}

const char *
eos_app_list_model_get_app_description (EosAppListModel *model,
                                        const char *app_id)
{
  return NULL;
}

const char *
eos_app_list_model_get_app_icon_name (EosAppListModel *model,
                                      const char *app_id,
                                      EosAppIconState icon_state)
{
  GDesktopAppInfo *info;
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), NULL);
  g_return_val_if_fail (app_id != NULL, NULL);

  info = eos_app_list_model_get_app_info (model, app_id);
  if (info == NULL)
    return NULL;

  return g_desktop_app_info_get_string (info, G_KEY_FILE_DESKTOP_KEY_ICON);
}

EosAppState
eos_app_list_model_get_app_state (EosAppListModel *model,
                                  const char *app_id)
{
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), EOS_APP_STATE_UNKNOWN);
  g_return_val_if_fail (app_id != NULL, EOS_APP_STATE_UNKNOWN);

  if (is_app_installed (model, app_id))
    return EOS_APP_STATE_INSTALLED;

  if (eos_app_list_model_get_app_info (model, app_id) != NULL)
    return EOS_APP_STATE_UNINSTALLED;

  return EOS_APP_STATE_UNKNOWN;
}

gboolean
eos_app_list_model_get_app_visible (EosAppListModel *model,
                                    const char *app_id)
{
  GDesktopAppInfo *info;
  g_return_val_if_fail (EOS_IS_APP_LIST_MODEL (model), FALSE);
  g_return_val_if_fail (app_id != NULL, FALSE);

  info = eos_app_list_model_get_app_info (model, app_id);
  if (info == NULL)
    return FALSE;

  return !(g_desktop_app_info_get_nodisplay (info) ||
           g_desktop_app_info_get_is_hidden (info));
}

void
eos_app_list_model_install_app (EosAppListModel *model,
                                const char *app_id)
{
  if (is_app_installed (model, app_id))
    return;

  if (!add_app_to_shell (model, app_id))
    return;

  g_hash_table_add (model->installed_apps, g_strdup (app_id));
  save_installed_apps (model);
}

void
eos_app_list_model_update_app (EosAppListModel *model,
                               const char *app_id)
{
}

void
eos_app_list_model_uninstall_app (EosAppListModel *model,
                                  const char *app_id)
{
  if (!is_app_installed (model, app_id))
    return;

  if (!remove_app_from_shell (model, app_id))
    return;

  g_hash_table_remove (model->installed_apps, app_id);
  save_installed_apps (model);
}
