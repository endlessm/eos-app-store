/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef __EOS_APP_LIST_MODEL_H__
#define __EOS_APP_LIST_MODEL_H__

#include <gio/gio.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

#define EOS_TYPE_APP_LIST_MODEL         (eos_app_list_model_get_type ())
#define EOS_APP_LIST_MODEL(obj)         (G_TYPE_CHECK_INSTANCE_CAST ((obj), EOS_TYPE_APP_LIST_MODEL, EosAppListModel))
#define EOS_IS_APP_LIST_MODEL(obj)      (G_TYPE_CHECK_INSTANCE_TYPE ((obj), EOS_TYPE_APP_LIST_MODEL))

typedef struct _EosAppListModel         EosAppListModel;
typedef struct _EosAppListModelClass    EosAppListModelClass;

GType eos_app_list_model_get_type (void);

EosAppListModel *eos_app_list_model_new (void);

void eos_app_list_model_load (EosAppListModel *model,
                              GCancellable    *cancellable,
                              GAsyncReadyCallback  callback,
                              gpointer             user_data);
GList *eos_app_list_model_load_finish (EosAppListModel  *model,
                                       GAsyncResult     *result,
                                       GError          **error);

const char *eos_app_list_model_get_app_name (EosAppListModel *model, const char *app_id);
const char *eos_app_list_model_get_app_description (EosAppListModel *model, const char *app_id);
const char *eos_app_list_model_get_app_comment (EosAppListModel *model, const char *app_id);
const char *eos_app_list_model_get_app_executable (EosAppListModel *model, const char *app_id);
const char *eos_app_list_model_get_app_icon_name (EosAppListModel *model,
                                                  const char *app_id,
                                                  EosAppIconState icon_state);
gboolean eos_app_list_model_get_app_visible (EosAppListModel *model, const char *app_id);
EosAppState eos_app_list_model_get_app_state (EosAppListModel *model, const char *app_id);

void eos_app_list_model_install_app (EosAppListModel *model, const char *app_id);
void eos_app_list_model_uninstall_app (EosAppListModel *model, const char *app_id);
void eos_app_list_model_update_app (EosAppListModel *mode, const char *app_id);

G_END_DECLS

#endif /* __EOS_APP_LIST_MODEL_H__ */
