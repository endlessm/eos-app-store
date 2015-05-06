/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <gio/gio.h>
#include <webkit2/webkit2.h>
#include "eos-app-enums.h"
#include "eos-app-info.h"

G_BEGIN_DECLS

char *  eos_app_get_content_dir  (void);

char *  eos_link_get_content_dir (void);

JsonArray * eos_app_parse_resource_content (const char *content_type,
                                            const char *content_name,
                                            GError **error_out);

GList * eos_link_load_content    (EosLinkCategory  category);

void    eos_app_load_screenshot  (GtkWidget       *image,
                                  const char      *path,
                                  int              width);

GdkPixbuf *eos_link_get_favicon  (WebKitWebView *webview);

void    eos_save_icon            (GdkPixbuf       *pixbuf,
                                  const gchar     *format,
                                  const gchar     *filename);

GdkNotifyType eos_get_event_notify_type (GdkEvent *event);

char *  eos_get_all_updates_uri (void);
char *  eos_get_updates_file (void);

char *  eos_get_updates_meta_record_uri (void);
char *  eos_get_updates_meta_record_file (void);

const char *eos_get_bundles_dir (void);
const char *eos_get_cache_dir (void);
const char *eos_get_bundle_download_dir (void);
void        eos_clear_bundle_download_dir (void);

gboolean eos_use_delta_updates (void);

gboolean eos_app_load_installed_apps (GHashTable *app_info,
                                      const char *appdir,
                                      GCancellable *cancellable,
                                      GError **error);
gboolean eos_app_load_available_apps (GHashTable *app_info,
                                      const char *data,
                                      GCancellable *cancellable,
                                      GError **error);
void eos_app_load_gio_apps   (GHashTable *app_info);
void eos_app_load_shell_apps (GHashTable *app_info,
                              GVariant *shell_apps);

int eos_compare_versions (const char *a,
                          const char *b);

EosAppCategory  eos_app_category_from_id (const char *p);

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
