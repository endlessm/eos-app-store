/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"
#include "eos-app-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <json-glib/json-glib.h>

#define APP_STORE_CONTENT_DIR   "application-store"

/**
 * eos_app_get_content_dir:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_get_content_dir (void)
{
  char *locale = g_strdup (setlocale (LC_MESSAGES, NULL));

  char *p;

  if ((p = strrchr (locale, '.')) != NULL)
    *p = '\0';

  char *res = g_build_filename (DATADIR,
                                APP_STORE_CONTENT_DIR,
                                locale,
                                "apps",
                                NULL);
  g_free (locale);

  return res;
}

void
eos_app_load_content (EosFlexyGrid *grid,
                      EosAppCategory category)
{
  g_return_if_fail (EOS_IS_FLEXY_GRID (grid));
  g_return_if_fail (category >= EOS_APP_CATEGORY_FEATURED &&
                    category <= EOS_APP_CATEGORY_UTILITIES);

  char *content_path = eos_app_get_content_dir ();
  g_assert (content_path != NULL);

  char *content_file = g_build_filename (content_path, "content.json", NULL);

  JsonParser *parser = json_parser_new ();

  GError *error = NULL;
  json_parser_load_from_file (parser, content_file, &error);
  if (error != NULL)
    {
      g_critical ("Unable to load content from '%s': %s", content_file, error->message);
      g_error_free (error);
      goto out;
    }

  JsonNode *node = json_parser_get_root (parser);
  if (!JSON_NODE_HOLDS_ARRAY (node))
    goto out;

  JsonArray *array = json_node_get_array (node);
  guint i, n_elements = json_array_get_length (array);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (array, i);

      EosAppInfo *info = eos_app_info_create_from_json (element);
      if (info == NULL)
        continue;

      if (category != EOS_APP_CATEGORY_FEATURED)
        {
          if (category != eos_app_info_get_category (info))
            {
              eos_app_info_unref (info);
              continue;
            }
        }
      else
        {
          if (!eos_app_info_is_featured (info))
            {
              eos_app_info_unref (info);
              continue;
            }
        }

      GtkWidget *cell = eos_app_info_create_cell (info);
      if (cell == NULL)
        {
          eos_app_info_unref (info);
          continue;
        }

      gtk_container_add (GTK_CONTAINER (grid), cell);
      gtk_widget_set_hexpand (cell, TRUE);
      gtk_widget_set_vexpand (cell, TRUE);
      gtk_widget_show_all (cell);

      eos_app_info_unref (info);
    }

out:
  g_object_unref (parser);
  g_free (content_file);
  g_free (content_path);
}
