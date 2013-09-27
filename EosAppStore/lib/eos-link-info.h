#ifndef EOS_LINK_INFO_H
#define EOS_LINK_INFO_H

#include <gdk-pixbuf/gdk-pixbuf.h>
#include <json-glib/json-glib.h>

G_BEGIN_DECLS

#define EOS_TYPE_LINK_INFO       (eos_link_info_get_type ())

typedef struct _EosLinkInfo      EosLinkInfo;

GType eos_link_info_get_type (void);

EosLinkInfo *   eos_link_info_new                 (void);
EosLinkInfo *   eos_link_info_ref                 (EosLinkInfo *info);
void            eos_link_info_unref               (EosLinkInfo *info);

const gchar *    eos_link_info_get_id             (EosLinkInfo *info);
const gchar *    eos_link_info_get_title          (EosLinkInfo *info);
const gchar *    eos_link_info_get_description    (EosLinkInfo *info);
GdkPixbuf   *    eos_link_info_get_thumbnail      (EosLinkInfo *info);
const gchar *    eos_link_info_get_url            (EosLinkInfo *info);

#ifndef __GI_SCANNER__

/* private */
G_GNUC_INTERNAL
EosLinkInfo *    eos_link_info_create_from_json   (JsonNode *node);

#endif

G_END_DECLS

#endif /* EOS_LINK_INFO_H */
