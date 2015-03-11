#ifndef EOS_APP_INFO_H
#define EOS_APP_INFO_H

#include <glib-object.h>
#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

#define EOS_TYPE_APP_INFO       (eos_app_info_get_type ())

typedef struct _EosAppInfo      EosAppInfo;

GType eos_app_info_get_type (void);

EosAppInfo *    eos_app_info_new                        (void);
EosAppInfo *    eos_app_info_ref                        (EosAppInfo *info);
void            eos_app_info_unref                      (EosAppInfo *info);

const char *    eos_app_info_get_title                  (const EosAppInfo *info);
const char *    eos_app_info_get_subtitle               (const EosAppInfo *info);
const char *    eos_app_info_get_desktop_id             (const EosAppInfo *info);
const char *    eos_app_info_get_description            (const EosAppInfo *info);

gboolean        eos_app_info_is_featured                (const EosAppInfo *info);
gboolean        eos_app_info_is_offline                 (const EosAppInfo *info);
EosAppCategory  eos_app_info_get_category               (const EosAppInfo *info);

char *          eos_app_info_get_square_img             (const EosAppInfo *info);
char *          eos_app_info_get_featured_img           (const EosAppInfo *info);

guint           eos_app_info_get_n_screenshots          (const EosAppInfo *info);
char **         eos_app_info_get_screenshots            (const EosAppInfo *info);

#ifndef __GI_SCANNER__

/* private */
G_GNUC_INTERNAL
EosAppInfo *    eos_app_info_create_from_content        (JsonNode *node);

#endif

G_END_DECLS

#endif /* EOS_APP_INFO_H */
