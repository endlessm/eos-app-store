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

typedef void (* EosProgressReportFunc) (EosAppInfo *info,
                                        goffset current,
                                        goffset total,
                                        gpointer user_data);

typedef void (* EosChunkFunc)          (GByteArray *chunk,
                                        gsize       chunk_len,
                                        gsize       bytes_read,
                                        gpointer    chunk_func_user_data);

typedef struct {
  EosAppListModel *model;
  EosAppInfo *info;
  goffset current;
  goffset total;
} EosProgressClosure;

typedef struct {
  EosProgressReportFunc  progress_func;
  gpointer               progress_func_user_data;
  EosAppInfo            *info;
  gsize                  total_len;
} EosDownloadAppFileClosure;

void      eos_net_utils_progress_closure_free    (gpointer data);

gboolean  eos_net_utils_download_file_from_uri   (SoupSession   *session,
                                                  const char    *content_type,
                                                  const char    *source_uri,
                                                  const char    *target_file,
                                                  char         **buffer,
                                                  gboolean       use_cache,
                                                  GCancellable  *cancellable,
                                                  GError       **error);

gboolean  eos_net_utils_download_file_with_retry (SoupSession          *session,
                                                  EosAppInfo           *info,
                                                  const char           *source_uri,
                                                  const char           *target_file,
                                                  EosProgressReportFunc progress_func,
                                                  gpointer              progress_func_user_data,
                                                  GCancellable         *cancellable,
                                                  GError              **error);

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
