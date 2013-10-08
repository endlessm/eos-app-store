/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <glib.h>
#include <endless/endless.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

char *  eos_app_get_content_dir  (void);

char *  eos_link_get_content_dir (void);

GList * eos_app_load_content     (EosAppCategory   category);

GList * eos_link_load_content    (EosLinkCategory  category);

void    eos_app_load_screenshot  (GtkWidget       *image,
                                  const char      *path,
                                  int              width);

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
