/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */
/* vim: set ai ts=2 sw=2 : */

#include "config.h"

#include "eos-app-utils.h"
#include "eos-downloader.h"

#include <stdlib.h>

static char **opt_app_ids;
static gboolean opt_use_delta;
static char *opt_output_dir = ".";

static const GOptionEntry opt_entries[] = {
  { "use-delta", 'd', 0, G_OPTION_ARG_NONE, &opt_use_delta, "Whether to download deltas, if they exist" },
  { "output-dir", 'o', 0, G_OPTION_ARG_FILENAME, &opt_output_dir, "Where to download bundles to", "PATH" },
  { G_OPTION_REMAINING, 0, 0, G_OPTION_ARG_STRING_ARRAY, &opt_app_ids, "Application id", "APPID" },
  { NULL },
};

static SoupSession *soup_session;
static GHashTable *apps;

static void
download_app (EosAppInfo *info)
{
  g_print (" downloading...\n");

  g_autoptr(GError) error = NULL;
  g_autofree char *bundle_path = eos_app_info_download_bundle (info, soup_session,
                                                               opt_output_dir, opt_use_delta,
                                                               NULL, NULL, NULL,
                                                               &error);
  if (error != NULL)
    {
      g_print ("downloading bundle failed: %s\n", error->message);
      return;
    }

  g_autofree char *sig_path = eos_app_info_download_signature (info, soup_session,
                                                               opt_output_dir, opt_use_delta,
                                                               NULL, &error);
  if (error != NULL)
    {
      g_print ("downloading signature failed: %s\n", error->message);
      return;
    }

  const char *checksum = eos_app_info_get_checksum (info, opt_use_delta, NULL);

  g_print ("  bundle   : %s\n"
           "  sig      : %s\n"
           "  checksum : %s - %s\n",
           bundle_path, sig_path, checksum,
           eos_app_utils_verify_checksum (bundle_path, checksum, NULL)
             ? "OK"
             : "FAIL");
}

static EosAppInfo *
get_app_info_for_app_id (const char *app_id)
{
  EosAppInfo *info;

  info = g_hash_table_lookup (apps, app_id);
  if (info)
    return info;

  g_autofree char *with_desktop = g_strconcat (app_id, ".desktop", NULL);
  info = g_hash_table_lookup (apps, with_desktop);
  if (info)
    return info;

  return NULL;
}

static void
download_app_id (const char *app_id)
{
  g_print ("%s:", app_id);

  EosAppInfo *info = get_app_info_for_app_id (app_id);
  if (info)
    download_app (info);
  else
    g_print ("\n"
             "  not found\n");

  g_print ("\n");
}

static gboolean
inited (gpointer user_data)
{
  g_autoptr(GError) error = NULL;
  g_autofree char *data;

  data = eos_refresh_available_apps (soup_session, NULL, &error);
  if (data != NULL)
    eos_app_load_available_apps_from_data (apps, data, NULL, &error);

  if (error != NULL)
    {
      g_printerr ("Could not load available apps: %s\n", error->message);
      exit (EXIT_FAILURE);
    }

  char **app_id;
  for (app_id = opt_app_ids; *app_id != NULL; app_id++)
    download_app_id (*app_id);

  exit (EXIT_SUCCESS);
  return G_SOURCE_REMOVE;
}

int main(int argc, char *argv[])
{
  g_autoptr(GOptionContext) context = g_option_context_new (NULL);
  g_option_context_add_main_entries (context, opt_entries, GETTEXT_PACKAGE);

  apps = g_hash_table_new_full (g_str_hash, g_str_equal,
                                g_free,
                                (GDestroyNotify) g_object_unref);
  soup_session = soup_session_new ();

  if (!g_option_context_parse (context, &argc, &argv, NULL))
    return EXIT_FAILURE;

  if (!opt_app_ids)
    return EXIT_FAILURE;

  g_autoptr(GMainLoop) loop = g_main_loop_new (NULL, FALSE);
  g_idle_add (inited, NULL);
  g_main_loop_run (loop);
  return EXIT_SUCCESS;
}
