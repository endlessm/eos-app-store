#ifndef EOS_APP_INFO_H
#define EOS_APP_INFO_H

#include <glib-object.h>
#include <gtk/gtk.h>
#include <json-glib/json-glib.h>

G_BEGIN_DECLS

#define EOS_TYPE_APP_INFO       (eos_app_info_get_type ())

typedef struct _EosAppInfo      EosAppInfo;

GType eos_app_info_get_type (void);

EosAppInfo *    eos_app_info_new                (void);
EosAppInfo *    eos_app_info_ref                (EosAppInfo *info);
void            eos_app_info_unref              (EosAppInfo *info);

const char *    eos_app_info_get_title          (const EosAppInfo *info);
const char *    eos_app_info_get_subtitle       (const EosAppInfo *info);
const char *    eos_app_info_get_desktop_id     (const EosAppInfo *info);
const char *    eos_app_info_get_description    (const EosAppInfo *info);

GtkWidget *     eos_app_info_create_cell        (const EosAppInfo *info);

#ifndef __GI_SCANNER__

/* private */
G_GNUC_INTERNAL
EosAppInfo *    eos_app_info_create_from_json   (JsonNode *node);

#endif

G_END_DECLS

#endif /* EOS_APP_INFO_H */
