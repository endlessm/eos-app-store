/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"
#include "eos-app-info.h"
#include "eos-link-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <json-glib/json-glib.h>

#define APP_STORE_CONTENT_DIR   "application-store"
#define APP_STORE_CONTENT_APPS  "apps"
#define APP_STORE_CONTENT_LINKS "links"

static char *
eos_get_content_dir (const gchar *content_type)
{
  char *res = g_build_filename (DATADIR,
                                APP_STORE_CONTENT_DIR,
                                eos_get_system_personality (),
                                content_type,
                                NULL);

  if (!g_file_test (res, G_FILE_TEST_EXISTS | G_FILE_TEST_IS_DIR))
    {
      g_free (res);

      res = g_build_filename (DATADIR,
                              APP_STORE_CONTENT_DIR,
                              "Default",
                              content_type,
                              NULL);
    }

  return res;
}

static const char *
eos_link_get_category_name (EosLinkCategory category)
{
  switch (category)
    {
    case EOS_LINK_CATEGORY_NEWS:
      return "News";

    case EOS_LINK_CATEGORY_SPORTS:
      return "Sports";

    case EOS_LINK_CATEGORY_EDUCATION:
      return "Education and Health";

    case EOS_LINK_CATEGORY_ENTERTAINMENT:
      return "Entertainment";

    case EOS_LINK_CATEGORY_LOCAL:
      return "Local";

    case EOS_LINK_CATEGORY_OPPORTUNITIES:
      return "Opportunities";

    default:
      return "";
    }
}

static JsonArray *
eos_app_parse_content (const char *content_type)
{
  JsonArray *content_array = NULL;
  GError *error = NULL;
  JsonParser *parser = json_parser_new ();

  char *content_path = eos_get_content_dir (content_type);
  char *content_file = g_build_filename (content_path, "content.json", NULL);

  json_parser_load_from_file (parser, content_file, &error);

  if (error != NULL)
    {
      g_critical ("Unable to load content from '%s': %s", content_file, error->message);
      g_error_free (error);
      goto out_error;
    }

  JsonNode *node = json_parser_get_root (parser);
  if (!JSON_NODE_HOLDS_ARRAY (node))
    {
      g_critical ("Expected array content");
      goto out_error;
    }

  content_array = json_node_dup_array (node);

 out_error:
  g_object_unref (parser);
  g_free (content_path);
  g_free (content_file);

  return content_array;
}

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
  return eos_get_content_dir (APP_STORE_CONTENT_APPS);
}

/**
 * eos_link_get_content_dir:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_link_get_content_dir (void)
{
  return eos_get_content_dir (APP_STORE_CONTENT_LINKS);
}

void
eos_app_load_content (EosFlexyGrid *grid,
                          EosAppCategory category)
{
  g_return_if_fail (EOS_IS_FLEXY_GRID (grid));
  g_return_if_fail (category >= EOS_APP_CATEGORY_FEATURED &&
                    category <= EOS_APP_CATEGORY_UTILITIES);

  JsonArray *array = eos_app_parse_content (APP_STORE_CONTENT_APPS);

  if (array == NULL)
    return;

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
  json_array_unref (array);
}

/**
 * eos_link_load_content:
 *
 * ...
 *
 * Returns: (element-type EosLinkInfo) (transfer full): ...
 */
GList *
eos_link_load_content (EosLinkCategory category)
{
  GList *links = NULL;
  JsonNode *element;
  JsonObject *obj;
  const gchar *category_name;

  JsonArray *categories_array = eos_app_parse_content (APP_STORE_CONTENT_LINKS);

  if (categories_array == NULL)
    return NULL;

  guint i, n_elements = json_array_get_length (categories_array);

  /* First contents are the categories; search for the interested one */
  category_name = eos_link_get_category_name (category);
  for (i = 0; i < n_elements; i++)
    {
      element = json_array_get_element (categories_array, i);
      if (!JSON_NODE_HOLDS_OBJECT (element))
        continue;

      obj = json_node_get_object (element);

      if (strcmp (json_node_get_string (json_object_get_member (obj, "category")), category_name) == 0)
        break;
    }

  if (i >= n_elements)
    {
      g_critical ("Unable to find category '%s'", category_name);
      goto out;
    }

  element = json_object_get_member (obj, "links");

  if (!JSON_NODE_HOLDS_ARRAY (element))
    {
      g_critical ("Category '%s' does not contain an array", category_name);
      goto out;
    }

  JsonArray *links_array = json_node_get_array (element);
  n_elements = json_array_get_length (links_array);

  for (i = 0; i < n_elements; i++)
    {
      element = json_array_get_element (links_array, i);
      EosLinkInfo *info = eos_link_info_create_from_json (element);
      if (info != NULL)
        links = g_list_prepend (links, info);
    }

out:
  json_array_unref (categories_array);

  return g_list_reverse (links);
}

void
eos_app_load_screenshot (GtkWidget  *image,
                         const char *path,
                         int         width)
{
  GError *error = NULL;
  GdkPixbuf *pixbuf =
    gdk_pixbuf_new_from_file_at_size (path, width, width, &error);

  if (error != NULL)
    {
      g_warning ("Cannot load image at path '%s': %s", path, error->message);
      g_error_free (error);
      gtk_widget_hide (image);
      return;
    }

  gtk_image_set_from_pixbuf (GTK_IMAGE (image), pixbuf);
  gtk_widget_show (image);

  g_object_unref (pixbuf);
}
