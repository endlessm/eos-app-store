/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <glib.h>
#include <endless/endless.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

char *  eos_app_get_app_content_dir  (void);

char *  eos_app_get_link_content_dir (void);

void    eos_app_load_app_content     (EosFlexyGrid   *grid,
                                      EosAppCategory  category);

GList * eos_app_load_link_content    (EosLinkCategory category);

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
