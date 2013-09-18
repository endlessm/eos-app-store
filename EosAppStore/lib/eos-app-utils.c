#include "config.h"

#include "eos-app-utils.h"

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

static EosFlexyShape
get_shape_from_id (const char *p)
{
  if (p == NULL || *p == '\0')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[0] != 'b')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[1] == '1' && p[2] == '\0')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[1] == '2')
    {
      if (p[2] == 'h' && p[3] == '\0')
        return EOS_FLEXY_SHAPE_MEDIUM_HORIZONTAL;

      if (p[2] == 'v' && p[3] == '\0')
        return EOS_FLEXY_SHAPE_MEDIUM_VERTICAL;
    }

  if (p[1] == '4' && p[2] == '\0')
    return EOS_FLEXY_SHAPE_LARGE;

  return EOS_FLEXY_SHAPE_SMALL;
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

      if (!JSON_NODE_HOLDS_OBJECT (element))
        continue;

      JsonObject *object = json_node_get_object (element);

      EosFlexyShape shape = get_shape_from_id (json_object_get_string_member (object, "display_shape"));

      GtkWidget *cell = g_object_new (EOS_TYPE_FLEXY_GRID_CELL,
                                      "shape", shape, 
                                      NULL);

      gtk_container_add (GTK_CONTAINER (grid), cell);
      gtk_widget_set_hexpand (cell, TRUE);
      gtk_widget_set_vexpand (cell, TRUE);

      GtkWidget *frame = gtk_frame_new (NULL);
      gtk_container_add (GTK_CONTAINER (cell), frame);

      GdkRGBA bg_color;
      gdk_rgba_parse (&bg_color, json_object_get_string_member (object, "color"));
      bg_color.alpha = 1.0;
      gtk_widget_override_background_color (frame, GTK_STATE_FLAG_NORMAL, &bg_color);

      GtkWidget *box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 6);
      gtk_widget_set_valign (box, GTK_ALIGN_END);
      gtk_container_add (GTK_CONTAINER (frame), box);

      GtkWidget *title = gtk_label_new (json_object_get_string_member (object, "title"));
      gtk_widget_set_halign (title, GTK_ALIGN_START);
      gtk_label_set_line_wrap (GTK_LABEL (title), TRUE);
      gtk_container_add (GTK_CONTAINER (box), title);

      GtkWidget *subtitle = gtk_label_new (json_object_get_string_member (object, "subtitle"));
      gtk_widget_set_halign (subtitle, GTK_ALIGN_START);
      gtk_label_set_line_wrap (GTK_LABEL (subtitle), TRUE);
      gtk_container_add (GTK_CONTAINER (box), subtitle);

      gtk_widget_show_all (cell);
    }

out:
  g_object_unref (parser);
  g_free (content_file);
  g_free (content_path);
}
