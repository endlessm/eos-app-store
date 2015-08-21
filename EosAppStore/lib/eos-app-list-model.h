/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef __EOS_APP_LIST_MODEL_H__
#define __EOS_APP_LIST_MODEL_H__

#include <gio/gio.h>
#include <gio/gdesktopappinfo.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#include "eos-app-enums.h"
#include "eos-app-info.h"

G_BEGIN_DECLS

#define EOS_TYPE_APP_LIST_MODEL         (eos_app_list_model_get_type ())
#define EOS_APP_LIST_MODEL(obj)         (G_TYPE_CHECK_INSTANCE_CAST ((obj), EOS_TYPE_APP_LIST_MODEL, EosAppListModel))
#define EOS_IS_APP_LIST_MODEL(obj)      (G_TYPE_CHECK_INSTANCE_TYPE ((obj), EOS_TYPE_APP_LIST_MODEL))

typedef struct _EosAppListModel         EosAppListModel;
typedef struct _EosAppListModelClass    EosAppListModelClass;

GType eos_app_list_model_get_type (void);

EosAppListModel *eos_app_list_model_new (void);

void eos_app_list_model_refresh_async               (EosAppListModel *model,
                                                     GCancellable *cancellable,
                                                     GAsyncReadyCallback callback,
                                                     gpointer user_data);

gboolean eos_app_list_model_refresh_finish          (EosAppListModel *model,
                                                     GAsyncResult *result,
                                                     GError **error);

GList * eos_app_list_model_get_apps_for_category    (EosAppListModel *model,
                                                     EosAppCategory category);

EosAppInfo * eos_app_list_model_create_from_filename (EosAppListModel *model,
                                                      const char *filename);

gboolean eos_app_list_model_get_app_has_launcher    (EosAppListModel *model,
                                                     const char *desktop_id);

gboolean eos_app_list_model_launch_app              (EosAppListModel *model,
                                                     const char *desktop_id,
                                                     guint32 timestamp,
                                                     GError **error);

void eos_app_list_model_install_app_async           (EosAppListModel *model,
                                                     const gchar *desktop_id,
                                                     GCancellable *cancellable,
                                                     GAsyncReadyCallback callback,
                                                     gpointer user_data);

gboolean eos_app_list_model_install_app_finish      (EosAppListModel *model,
                                                     GAsyncResult *result,
                                                     GError **error);

void eos_app_list_model_uninstall_app_async         (EosAppListModel *model,
                                                     const gchar *desktop_id,
                                                     GCancellable *cancellable,
                                                     GAsyncReadyCallback callback,
                                                     gpointer user_data);

gboolean eos_app_list_model_uninstall_app_finish    (EosAppListModel *model,
                                                     GAsyncResult *result,
                                                     GError **error);

void eos_app_list_model_update_app_async            (EosAppListModel *model,
                                                     const gchar *desktop_id,
                                                     GCancellable *cancellable,
                                                     GAsyncReadyCallback callbcak,
                                                     gpointer user_data);

gboolean eos_app_list_model_update_app_finish       (EosAppListModel *model,
                                                     GAsyncResult *result,
                                                     GError **error);

G_END_DECLS

#endif /* __EOS_APP_LIST_MODEL_H__ */
