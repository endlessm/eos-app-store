/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef EOS_APP_UTILS_H
#define EOS_APP_UTILS_H

#include <glib.h>
#include <endless/endless.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

char *  eos_app_get_content_dir (void);

void    eos_app_load_content    (EosFlexyGrid   *grid,
                                 EosAppCategory  category);

G_END_DECLS

#endif /* EOS_APP_UTILS_H */
