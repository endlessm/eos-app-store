/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include <webkit2/webkit2.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

JsonArray * eos_app_parse_resource_content (const char *content_type,
                                            const char *content_name,
                                            GError **error_out);

GList * eos_link_load_content    (EosLinkCategory  category);

GdkPixbuf *eos_link_get_favicon  (WebKitWebView *webview);

void    eos_save_icon            (GdkPixbuf       *pixbuf,
                                  const gchar     *format,
                                  const gchar     *filename);

#define EOS_APP_UTILS_ERROR        (eos_app_utils_error_quark ())

GQuark eos_app_utils_error_quark (void);

typedef enum {
  EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_STRUCTURE,
  EOS_APP_UTILS_ERROR_JSON_MISSING_ATTRIBUTE,
  EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_VALUE
} EosAppUtilsError;

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
