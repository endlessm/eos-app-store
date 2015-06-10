/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#ifndef __EOS_NET_UTILS_H__
#define __EOS_NET_UTILS_H__

#include <glib.h>
#include <glib-object.h>

#include "eos-app-info.h"
#include "eos-app-list-model.h"

G_BEGIN_DECLS

typedef void (* EosProgressReportFunc) (EosAppInfo *info,
                                        goffset current,
                                        goffset total,
                                        gpointer user_data);

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

void   eos_net_utils_progress_closure_free   (gpointer data);

G_END_DECLS

#endif /* __EOS_NET_UTILS_H__ */
