#include "config.h"

#include "eos-app-list-model.h"

#include <glib-object.h>

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gmenu-tree.h>

struct _EosAppListModel
{
  GObject parent_instance;

  GMenuTree *app_tree;

  GMutex apps_by_id_lock;
  GHashTable *apps_by_id;
};

struct _EosAppListModelClass
{
  GObjectClass parent_class;
};

G_DEFINE_TYPE (EosAppListModel, eos_app_list_model, G_TYPE_OBJECT)

static void
on_app_tree_changed (GMenuTree       *tree,
                     EosAppListModel *self)
{
}

static void
eos_app_list_model_finalize (GObject *gobject)
{
  EosAppListModel *self = EOS_APP_LIST_MODEL (gobject);

  g_clear_object (&self->app_tree);
  g_mutex_clear (&self->apps_by_id_lock);
  g_hash_table_unref (self->apps_by_id);

  G_OBJECT_CLASS (eos_app_list_model_parent_class)->finalize (gobject);
}

static void
eos_app_list_model_class_init (EosAppListModelClass *klass)
{
  G_OBJECT_CLASS (klass)->finalize = eos_app_list_model_finalize;
}

static void
eos_app_list_model_init (EosAppListModel *self)
{
  self->app_tree =
    gmenu_tree_new ("gnome-applications.menu", GMENU_TREE_FLAGS_INCLUDE_NODISPLAY);

  g_mutex_init (&self->apps_by_id_lock);
}

EosAppListModel *
eos_app_list_model_new (void)
{
  return g_object_new (EOS_TYPE_APP_LIST_MODEL, NULL);
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

  g_mutex_lock (&model->apps_by_id_lock);

  if (model->apps_by_id != NULL)
    {
      g_hash_table_unref (model->apps_by_id);
      model->apps_by_id = NULL;
    }

  if (!gmenu_tree_load_sync (model->app_tree, &error))
    {
      g_mutex_unlock (&model->apps_by_id_lock);
      g_task_return_error (task, error);
      return;
    }

  set = g_hash_table_new_full (g_str_hash, g_str_equal,
                               NULL,
                               gmenu_tree_item_unref);

  root = gmenu_tree_get_root_directory (model->app_tree);
  if (root == NULL)
    {
      g_mutex_unlock (&model->apps_by_id_lock);
      g_task_return_pointer (task, NULL, NULL);
      return;
    }

  flatten_menu_tree_recursive (root, set);

  gmenu_tree_item_unref (root);

  model->apps_by_id = set;

  g_mutex_unlock (&model->apps_by_id_lock);
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

static GDesktopAppInfo *
eos_app_list_model_get_app_info (EosAppListModel *model,
                                 const char *app_id)
{
  GMenuTreeEntry *entry;
  GDesktopAppInfo *res;

  if (model->apps_by_id == NULL)
    {
      g_critical ("The application list is not loaded.");
      return NULL;
    }

  g_mutex_lock (&model->apps_by_id_lock);
  entry = g_hash_table_lookup (model->apps_by_id, app_id);
  if (entry == NULL)
    {
      g_mutex_unlock (&model->apps_by_id_lock);
      g_critical ("No application '%s' was found.", app_id);
      return NULL;
    }

  res = gmenu_tree_entry_get_app_info (entry);
  g_mutex_unlock (&model->apps_by_id_lock);

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
