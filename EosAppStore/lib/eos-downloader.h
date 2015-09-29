/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#pragma once

#include <glib.h>
#include <glib-object.h>
#include <libsoup/soup.h>
#include "eos-app-info.h"

char * eos_app_info_download_signature (EosAppInfo *info,
                                        SoupSession *soup_session,
                                        const char *download_dir,
                                        gboolean use_delta,
                                        GCancellable *cancellable,
                                        GError **error_out);

char * eos_app_info_download_bundle (EosAppInfo *info,
                                     SoupSession *soup_session,
                                     const char *download_dir,
                                     gboolean use_delta,
                                     GCancellable *cancellable,
                                     GFileProgressCallback progress_callback,
                                     gpointer progress_user_data,
                                     GError **error_out);

char * eos_refresh_available_apps (SoupSession *soup_session,
                                   GCancellable *cancellable,
                                   GError **error_out);
