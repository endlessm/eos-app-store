/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#ifndef __EOS_NET_UTILS_H__
#define __EOS_NET_UTILS_H__

#include <glib.h>
#include <glib-object.h>
#include <libsoup/soup.h>

#include "eos-app-info.h"
#include "eos-app-list-model.h"

G_BEGIN_DECLS

void      eos_net_utils_progress_closure_free    (gpointer data);

gboolean  eos_net_utils_download_file (SoupSession   *session,
                                       const char    *content_type,
                                       const char    *source_uri,
                                       const char    *target_file,
                                       char         **buffer,
                                       gboolean       use_cache,
                                       GCancellable  *cancellable,
                                       GError       **error);

gboolean  eos_net_utils_download_file_with_retry (SoupSession           *session,
                                                  const char            *source_uri,
                                                  const char            *target_file,
                                                  GFileProgressCallback  progress_func,
                                                  gpointer               progress_func_user_data,
                                                  GCancellable          *cancellable,
                                                  GError               **error);

SoupLogger * eos_net_utils_add_soup_logger          (SoupSession *session);

void         eos_net_utils_remove_soup_logger       (SoupSession *session,
                                                     SoupLogger *logger);

#define EOS_NET_UTILS_ERROR        (eos_net_utils_error_quark ())

GQuark eos_net_utils_error_quark (void);

typedef enum {
  EOS_NET_UTILS_ERROR_INVALID_URL,
  EOS_NET_UTILS_ERROR_FAILED,
  EOS_NET_UTILS_ERROR_BAD_CERTIFICATE,
  EOS_NET_UTILS_ERROR_CANCELLED
} EosNetUtilsError;

G_END_DECLS

#endif /* __EOS_NET_UTILS_H__ */
