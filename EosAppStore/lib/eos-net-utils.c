/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include <glib.h>

#include "eos-net-utils.h"

void
eos_net_utils_progress_closure_free (gpointer _data)
{
  EosProgressClosure *data = _data;

  g_clear_object (&data->model);
  eos_app_info_unref (data->info);

  g_slice_free (EosProgressClosure, data);
}
