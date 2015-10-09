/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <gio/gio.h>
#include <webkit2/webkit2.h>
#include "eos-app-enums.h"
#include "eos-app-info.h"
#include "eos-app-manager-service.h"

G_BEGIN_DECLS

JsonArray * eos_app_parse_resource_content (const char *content_type,
                                            const char *content_name,
                                            GError **error_out);

GList * eos_link_load_content    (EosLinkCategory  category);

void    eos_app_load_screenshot  (GtkWidget       *image,
                                  const char      *resource_path,
                                  int              width);

GdkPixbuf *eos_link_get_favicon  (WebKitWebView *webview);

void    eos_save_icon            (GdkPixbuf       *pixbuf,
                                  const gchar     *format,
                                  const gchar     *filename);

GdkNotifyType eos_get_event_notify_type (GdkEvent *event);

char *  eos_get_all_updates_uri                 (void);
char *  eos_get_updates_file                    (void);

char *  eos_get_updates_meta_record_uri         (void);
char *  eos_get_updates_meta_record_file        (void);

const char *eos_get_bundles_dir                 (void);
const char *eos_get_cache_dir                   (void);
char       *eos_get_bundle_download_dir         (const char *app_id,
                                                 const char *version);
const char *eos_get_app_server_url              (void);
const char *eos_get_primary_storage             (void);
const char *eos_get_secondary_storage           (void);
gboolean    eos_has_secondary_storage           (void);

gboolean eos_use_delta_updates                  (void);

gboolean eos_app_load_installed_apps      (GHashTable    *app_info,
                                           GCancellable  *cancellable);

gboolean eos_app_load_available_apps      (GHashTable    *app_info,
                                           GCancellable  *cancellable,
                                           GError       **error);
gboolean eos_app_load_available_apps_from_data (GHashTable    *app_info,
                                                const char    *data,
                                                GCancellable  *cancellable,
                                                GError       **error);

gboolean eos_app_load_updates_meta_record (gint64        *monotonic_update_id,
                                           const char    *data,
                                           GCancellable  *cancellable,
                                           GError       **error);

gboolean eos_check_available_space        (const char    *path,
                                           goffset        min_size,
                                           GCancellable  *cancellable,
                                           GError       **error);

gboolean eos_mkdir_for_artifact           (const char *target_file,
                                           GError    **error);

void eos_app_load_gio_apps   (GHashTable *app_info);
void eos_app_load_shell_apps (GHashTable *app_info,
                              GVariant *shell_apps);

int eos_compare_versions (const char *a,
                          const char *b);

EosAppCategory  eos_app_category_from_id (const char *p);

char * eos_storage_type_to_string (EosStorageType storage);

#define EOS_APP_UTILS_ERROR        (eos_app_utils_error_quark ())

GQuark eos_app_utils_error_quark (void);

EosAppManager * eos_get_eam_dbus_proxy (void);

typedef enum {
  EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_STRUCTURE,
  EOS_APP_UTILS_ERROR_JSON_MISSING_ATTRIBUTE,
  EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_VALUE
} EosAppUtilsError;

gboolean eos_app_utils_verify_checksum (const char *bundle_file,
                                        const char *checksum_str,
                                        GError **error);

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
