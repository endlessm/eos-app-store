#ifndef __EOS_APP_LIST_MODEL_H__
#define __EOS_APP_LIST_MODEL_H__

#include <gio/gio.h>

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
GHashTable *eos_app_list_model_load_finish (EosAppListModel  *model,
                                            GAsyncResult     *result,
                                            GError          **error);

G_END_DECLS

#endif /* __EOS_APP_LIST_MODEL_H__ */
