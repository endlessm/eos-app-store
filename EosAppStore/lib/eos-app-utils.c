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

/**
 * eos_app_load_content:
 * @category: ...
 *
 * ...
 *
 * Return value: (transfer full) (element-type EosAppInfo): ...
 */
GList *
eos_app_load_content (EosAppCategory category)
{
  JsonArray *array = eos_app_parse_content (APP_STORE_CONTENT_APPS);

  if (array == NULL)
    return NULL;

  GList *infos = NULL;

  guint i, n_elements = json_array_get_length (array);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (array, i);

      EosAppInfo *info = eos_app_info_create_from_json (element);
      if (info == NULL)
        continue;

      if (category == EOS_APP_CATEGORY_MY_APPLICATIONS)
        {
          /* do nothing */
        }
      else if (category == EOS_APP_CATEGORY_FEATURED)
        {
          if (!eos_app_info_is_featured (info))
            {
              eos_app_info_unref (info);
              continue;
            }
        }
      else
        {
          if (category != eos_app_info_get_category (info))
            {
              eos_app_info_unref (info);
              continue;
            }

        }

      infos = g_list_prepend (infos, info);
    }

  json_array_unref (array);

  return g_list_reverse (infos);
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

/**
 * eos_link_get_favicon:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
GdkPixbuf *
eos_link_get_favicon (WebKitWebView *webview)
{
  GdkPixbuf *dest;
  cairo_surface_t *icon_surface = webkit_web_view_get_favicon (webview);

  if (icon_surface == NULL)
    return NULL;

  gint favicon_width = cairo_image_surface_get_width (icon_surface);
  gint favicon_height = cairo_image_surface_get_height (icon_surface);
  gint biggest =  MAX (favicon_width, favicon_height);
  gdouble scale = 1.0;
  gdouble offset_x = 0.0;
  gdouble offset_y = 0.0;
  GdkPixbuf *base = NULL;

  /* If size is > 64px, resize it to 64px */
  if (biggest >= 64)
    {
      scale = (gdouble) 64 / biggest;
    }
  /* If size is between [16px, 64px], center in the placeholder icon.
     Additionally, if between [48px, 64px] resize it to 48px. */
  else if (biggest > 16)
    {
      if (biggest >= 48)
        {
          scale = (gdouble) 48 / biggest;
          favicon_width *= scale;
          favicon_height *= scale;
        }

      offset_x = (64 - favicon_width) / 2;
      offset_y = (64 - favicon_height) / 2;

      base = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_big-icon.png", NULL);
    }
  /* Otherwise keep the same size. But as the holder for the icon
     in the shell is 64x64, and shell scales the desktop icons,
     let's put the icon inside a canvas of 64x64,
     so the shell does not scale it */
  else
    {
      offset_x = (64 - favicon_width) / 2;
      offset_y = (64 - favicon_height) / 2;
      base = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_favicon.png", NULL);
    }

  cairo_surface_t *dest_surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, 64, 64);
  cairo_t *cr = cairo_create (dest_surface);

  if (base != NULL)
    {
      gdk_cairo_set_source_pixbuf (cr, base, 0, 0);
      cairo_paint (cr);
      g_object_unref (base);
    }

  cairo_pattern_t *icon_pattern = cairo_pattern_create_for_surface (icon_surface);
  cairo_matrix_t matrix;

  cairo_matrix_init_scale (&matrix, 1.0 / scale, 1.0 / scale);
  cairo_matrix_translate (&matrix, - offset_x, - offset_y);
  cairo_pattern_set_matrix (icon_pattern, &matrix);

  cairo_set_source (cr, icon_pattern);
  cairo_paint (cr);

  dest = gdk_pixbuf_get_from_surface (dest_surface, 0, 0, 64, 64);
  cairo_surface_destroy (dest_surface);
  cairo_pattern_destroy (icon_pattern);
  cairo_destroy (cr);

  return dest;
}

void
eos_save_icon (GdkPixbuf *pixbuf,
               const gchar *format,
               const gchar *filename)
{
  gdk_pixbuf_save (pixbuf, filename, format, NULL, NULL);
}
