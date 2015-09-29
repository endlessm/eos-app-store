#ifndef EOS_APP_INFO_H
#define EOS_APP_INFO_H

#include <glib-object.h>
#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include <gio/gdesktopappinfo.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

#define EOS_TYPE_APP_INFO       (eos_app_info_get_type ())

typedef struct _EosAppInfo      EosAppInfo;
typedef struct _EosAppInfoClass EosAppInfoClass;

GType eos_app_info_get_type (void);

EosAppInfo *    eos_app_info_new                        (const char *application_id);

const char *    eos_app_info_get_application_id         (const EosAppInfo *info);
const char *    eos_app_info_get_desktop_id             (const EosAppInfo *info);
const char *    eos_app_info_get_content_id             (const EosAppInfo *info);
const char *    eos_app_info_get_title                  (const EosAppInfo *info);
const char *    eos_app_info_get_subtitle               (const EosAppInfo *info);
const char *    eos_app_info_get_description            (const EosAppInfo *info);
const char *    eos_app_info_get_installed_version      (const EosAppInfo *info);
const char *    eos_app_info_get_available_version      (const EosAppInfo *info);
gint64          eos_app_info_get_installed_size         (const EosAppInfo *info);
const char *    eos_app_info_get_locale                 (const EosAppInfo *info);

gboolean        eos_app_info_is_featured                (const EosAppInfo *info);
gboolean        eos_app_info_is_offline                 (const EosAppInfo *info);
EosStorageType  eos_app_info_get_storage_type           (const EosAppInfo *info);
EosStorageType  eos_app_info_get_install_storage_type   (const EosAppInfo *info);
EosAppCategory  eos_app_info_get_category               (const EosAppInfo *info);

char *          eos_app_info_get_square_img             (const EosAppInfo *info);
char *          eos_app_info_get_featured_img           (const EosAppInfo *info);
char *          eos_app_info_get_icon_name              (const EosAppInfo *info);

const char *    eos_app_info_get_bundle_uri             (const EosAppInfo *info);
const char *    eos_app_info_get_signature_uri          (const EosAppInfo *info);
const char *    eos_app_info_get_bundle_hash            (const EosAppInfo *info);

const char *    eos_app_info_get_delta_bundle_uri       (const EosAppInfo *info);
const char *    eos_app_info_get_delta_signature_uri    (const EosAppInfo *info);
const char *    eos_app_info_get_delta_bundle_hash      (const EosAppInfo *info);
gboolean        eos_app_info_get_has_delta_update       (const EosAppInfo *info);

guint           eos_app_info_get_n_screenshots          (const EosAppInfo *info);
char **         eos_app_info_get_screenshots            (const EosAppInfo *info);

gboolean        eos_app_info_is_installable             (const EosAppInfo *info);
gboolean        eos_app_info_is_installed               (const EosAppInfo *info);
gboolean        eos_app_info_is_available               (const EosAppInfo *info);
gboolean        eos_app_info_is_updatable               (const EosAppInfo *info);
gboolean        eos_app_info_is_removable               (const EosAppInfo *info);

gboolean        eos_app_info_get_has_launcher           (const EosAppInfo *info);
EosAppState     eos_app_info_get_state                  (const EosAppInfo *info);
gboolean        eos_app_info_check_install_space        (const EosAppInfo *info);

gint64          eos_app_info_get_installation_time      (const EosAppInfo *info);
const char *    eos_app_info_get_checksum               (const EosAppInfo *info,
                                                         gboolean          use_delta,
                                                         GError          **error);

#ifndef __GI_SCANNER__

/* private */
G_GNUC_INTERNAL
gboolean        eos_app_info_update_from_content        (EosAppInfo *info,
                                                         JsonObject *obj);
G_GNUC_INTERNAL
gboolean        eos_app_info_update_from_server         (EosAppInfo *info,
                                                         JsonObject *obj);
G_GNUC_INTERNAL
gboolean        eos_app_info_update_from_installed      (EosAppInfo *info,
                                                         const char *filename);
G_GNUC_INTERNAL
void            eos_app_info_update_from_gio            (EosAppInfo *info,
                                                         GDesktopAppInfo *desktop_info);
G_GNUC_INTERNAL
void            eos_app_info_clear_server_update_attributes (EosAppInfo *info);

G_GNUC_INTERNAL
void            eos_app_info_set_has_launcher           (EosAppInfo *info,
                                                         gboolean    has_launcher);
G_GNUC_INTERNAL
void            eos_app_info_set_is_installed           (EosAppInfo *info,
                                                         gboolean    is_installed);
G_GNUC_INTERNAL
gboolean        eos_app_info_installed_changed          (EosAppInfo *info);

#endif

G_END_DECLS

#endif /* EOS_APP_INFO_H */
