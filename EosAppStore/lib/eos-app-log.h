/* Copyright 2015 Endless Mobile, Inc. */

#ifndef EAS_LOG_H
#define EAS_LOG_H

#include <glib.h>

G_BEGIN_DECLS

void      eos_app_log_debug_message       (const char *fmt,
                                           ...) G_GNUC_PRINTF (1, 2);
void      eos_app_log_error_message       (const char *fmt,
                                           ...) G_GNUC_PRINTF (1, 2);
void      eos_app_log_info_message        (const char *fmt,
                                           ...) G_GNUC_PRINTF (1, 2);

gboolean  eos_app_log_soup_debug_enabled  (void);

G_END_DECLS

#endif /* EAS_LOG_H */
