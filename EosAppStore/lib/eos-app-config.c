/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include <glib.h>

#include "config.h"
#include "eos-app-config.h"
#include "eos-app-log.h"

#define CONFIG_FILE "settings.conf"

#define CONFIG_CACHE_DIR "cache_dir"

char *
eos_app_config_get_cache_dir (void)
{
  GKeyFile *keyfile = NULL;
  GKeyFileFlags flags;
  GError *error;

  char *config_dir;
  char *settings_file;
  char *settings_data = NULL;
  char *cache_dir;
  char *start_group = NULL;
  gsize size;

  eos_app_log_info_message ("Trying to load configuration file");
  settings_file = g_build_filename (g_get_user_config_dir (),
                                    PACKAGE,
                                    CONFIG_FILE,
                                    NULL);

  /* Create a keyfile object */
  keyfile = g_key_file_new();
  flags = G_KEY_FILE_KEEP_COMMENTS | G_KEY_FILE_KEEP_TRANSLATIONS;

  start_group = g_key_file_get_start_group (keyfile);

  /* Try to populate the config data from our settings file */
  if (!g_key_file_load_from_file (keyfile, settings_file, flags, &error)) {
    eos_app_log_info_message ("Configuration file failed to load - (re)creating it");

    /* Create the directory to store the config file if it's not there already */
    config_dir = g_path_get_dirname (settings_file);
    g_mkdir_with_parents (config_dir, 0755);
    g_free (config_dir);

    /* Assemble the template that will be the name of our cache dir */
    char *cache_dir_filename = g_strconcat (PACKAGE, "-XXXXXX", NULL);
    char *cache_dir_template = g_build_filename (BUNDLEDIR, cache_dir_filename, NULL);
    g_free (cache_dir_filename);

     /* Create the cache dir */
    cache_dir = g_mkdtemp_full (cache_dir_template, 0755);

    g_key_file_set_string(keyfile, start_group, CONFIG_CACHE_DIR, cache_dir);

    settings_data = g_key_file_to_data (keyfile, &size, &error);
    if (!settings_data) {
      eos_app_log_error_message ("Could not serialized config data: %s", error->message);
      g_error_free (error);
    } else {
      if (!g_file_set_contents (settings_file, settings_data, size,  &error)) {
        eos_app_log_error_message ("Could not write config file: %s", error->message);
        g_error_free (error);
      }
      g_free (settings_data);
    }

    g_free (cache_dir);
  }
  g_free(settings_file);

  cache_dir = g_key_file_get_string (keyfile, start_group, CONFIG_CACHE_DIR,
                                      &error);
  g_free (start_group);

  eos_app_log_info_message ("Using %s as the download directory", cache_dir);

  return cache_dir;
}
