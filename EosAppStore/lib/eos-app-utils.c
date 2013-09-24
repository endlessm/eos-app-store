/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"
#include "eos-app-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <json-glib/json-glib.h>

#define APP_STORE_CONTENT_DIR   "application-store"

/* Keep in the same order as the EosAppCategory enumeration */
static const struct {
  const EosAppCategory category;
  const char *directory;
} categories[] = {
  /* Translators: use the same string used to install the app store content JSON */
  { EOS_APP_CATEGORY_FEATURED,  N_("Featured") },
  { EOS_APP_CATEGORY_EDUCATION, N_("Education") },
  { EOS_APP_CATEGORY_LEISURE,   N_("Leisure") },
  { EOS_APP_CATEGORY_UTILITIES, N_("Utilities") },
};

static const char *
get_category_dir (EosAppCategory category)
{
  g_assert (category >= EOS_APP_CATEGORY_FEATURED &&
            category <= EOS_APP_CATEGORY_UTILITIES);

  return gettext (categories[category].directory);
}

/**
 * eos_app_get_content_dir:
 *
 * Retrieves the directory with the content for the given category, taking into account
 * the system locale.
 *
 * Returns: (transfer full):
 */
char *
eos_app_get_content_dir (EosAppCategory category)
{
  char *locale = g_strdup (setlocale (LC_MESSAGES, NULL));

  char *p;

  if ((p = strrchr (locale, '.')) != NULL)
    *p = '\0';

  char *res = g_build_filename (DATADIR,
                                APP_STORE_CONTENT_DIR,
                                locale,
                                get_category_dir (category),
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

  char *content_path = eos_app_get_content_dir (category);
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

      GtkWidget *cell = eos_app_info_create_cell (info);
      if (cell == NULL)
        continue;

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
