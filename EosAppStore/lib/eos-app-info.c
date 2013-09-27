#include "config.h"

#include "eos-app-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <endless/endless.h>

#include "eos-app-utils.h"

/*
 * EosAppCell
 */

enum {
  PROP_0,
  PROP_DESKTOP_ID,
  PROP_TITLE,
  PROP_SUBTITLE,
  PROP_APP_INFO,
  NUM_PROPS
};

typedef struct {
  EosFlexyGridCell parent;

  char *desktop_id;

  GtkWidget *title_label;
  GtkWidget *subtitle_label;

  EosAppInfo *info;

  GdkPixbuf *image;
} EosAppCell;

typedef EosFlexyGridCellClass EosAppCellClass;

static GParamSpec *eos_app_cell_props[NUM_PROPS] = { NULL, };

static GType eos_app_cell_get_type (void) G_GNUC_CONST;

G_DEFINE_TYPE (EosAppCell, eos_app_cell, EOS_TYPE_FLEXY_GRID_CELL)

static void
eos_app_cell_get_property (GObject    *gobject,
                           guint       prop_id,
                           GValue     *value,
                           GParamSpec *pspec)
{
  EosAppCell *self = (EosAppCell *) gobject;

  switch (prop_id)
    {
    case PROP_DESKTOP_ID:
      g_value_set_string (value, self->desktop_id);
      break;

    case PROP_TITLE:
      g_value_set_string (value, gtk_label_get_text (GTK_LABEL (self->title_label)));
      break;

    case PROP_SUBTITLE:
      g_value_set_string (value, gtk_label_get_text (GTK_LABEL (self->subtitle_label)));
      break;

    case PROP_APP_INFO:
      g_value_set_boxed (value, self->info);
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_app_cell_set_property (GObject      *gobject,
                           guint         prop_id,
                           const GValue *value,
                           GParamSpec   *pspec)
{
  EosAppCell *self = (EosAppCell *) gobject;

  switch (prop_id)
    {
    case PROP_DESKTOP_ID:
      g_free (self->desktop_id);
      self->desktop_id = g_value_dup_string (value);
      break;

    case PROP_TITLE:
      gtk_label_set_text (GTK_LABEL (self->title_label), g_value_get_string (value));
      break;

    case PROP_SUBTITLE:
      gtk_label_set_text (GTK_LABEL (self->subtitle_label), g_value_get_string (value));
      break;

    case PROP_APP_INFO:
      g_assert (self->info == NULL);
      self->info = eos_app_info_ref (g_value_get_boxed (value));
      g_assert (self->info != NULL);
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_app_cell_finalize (GObject *gobject)
{
  EosAppCell *self = (EosAppCell *) gobject;

  g_clear_object (&self->image);
  g_free (self->desktop_id);
  eos_app_info_unref (self->info);

  G_OBJECT_CLASS (eos_app_cell_parent_class)->finalize (gobject);
}

static gboolean
eos_app_cell_draw (GtkWidget *widget,
                   cairo_t   *cr)
{
  EosAppCell *self = (EosAppCell *) widget;
  GtkAllocation allocation;
  GError *error;
  char *path;

  if (self->info == NULL)
    {
      g_critical ("No EosAppInfo found for cell %p", widget);
      return FALSE;
    }

  if (self->image != NULL)
    goto out;

  gtk_widget_get_allocation (widget, &allocation);

  if (eos_app_info_is_featured (self->info))
    path = eos_app_info_get_featured_img (self->info);
  else
    path = eos_app_info_get_square_img (self->info);

  if (path == NULL)
    {
      g_warning ("No image found for app info '%s'[%p]",
                 eos_app_info_get_title (self->info),
                 self->info);
      goto out;
    }

  int width = allocation.width;
  int height = allocation.height;

  error = NULL;
  self->image = gdk_pixbuf_new_from_file_at_size (path, width, height, &error);
  if (error != NULL)
    {
      g_warning ("Unable to load image at path '%s': %s",
                 path, error->message);
      g_error_free (error);
    }

  g_free (path);

out:
  if (self->image != NULL)
    gtk_render_icon (gtk_widget_get_style_context (widget),
                     cr,
                     self->image,
                     0.0, 0.0);

  GTK_WIDGET_CLASS (eos_app_cell_parent_class)->draw (widget, cr);

  return FALSE;
}

static void
eos_app_cell_class_init (EosAppCellClass *klass)
{
  GObjectClass *oclass = G_OBJECT_CLASS (klass);
  GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

  oclass->set_property = eos_app_cell_set_property;
  oclass->get_property = eos_app_cell_get_property;
  oclass->finalize = eos_app_cell_finalize;

  widget_class->draw = eos_app_cell_draw;

  eos_app_cell_props[PROP_DESKTOP_ID] =
    g_param_spec_string ("desktop-id",
                         "Desktop ID",
                         "The Desktop ID",
                         "",
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

  eos_app_cell_props[PROP_TITLE] =
    g_param_spec_string ("title",
                         "Title",
                         "Title of the app",
                         "",
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

  eos_app_cell_props[PROP_SUBTITLE] =
    g_param_spec_string ("subtitle",
                         "Subtitle",
                         "Subtitle of the app",
                         "",
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

  eos_app_cell_props[PROP_APP_INFO] =
    g_param_spec_boxed ("app-info",
                        "App Info",
                        "Application Info",
                        EOS_TYPE_APP_INFO,
                        G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS | G_PARAM_CONSTRUCT_ONLY);

  g_object_class_install_properties (oclass, NUM_PROPS, eos_app_cell_props);
}

static void
eos_app_cell_init (EosAppCell *self)
{
  gtk_widget_set_hexpand (GTK_WIDGET (self), TRUE);
  gtk_widget_set_vexpand (GTK_WIDGET (self), TRUE);

  GtkWidget *frame = gtk_frame_new (NULL);
  gtk_style_context_add_class (gtk_widget_get_style_context (frame),
                               "app-cell-frame");
  gtk_container_add (GTK_CONTAINER (self), frame);
  gtk_widget_show (frame);

  GtkWidget *box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 2);
  gtk_widget_set_valign (box, GTK_ALIGN_END);
  gtk_widget_set_halign (box, GTK_ALIGN_START);
  gtk_container_add (GTK_CONTAINER (frame), box);
  gtk_widget_show (box);

  self->title_label = gtk_label_new ("");
  gtk_style_context_add_class (gtk_widget_get_style_context (self->title_label),
                               "app-cell-title");
  gtk_label_set_line_wrap (GTK_LABEL (self->title_label), TRUE);
  gtk_misc_set_alignment (GTK_MISC (self->title_label), 0.0, 0.5);
  gtk_container_add (GTK_CONTAINER (box), self->title_label);
  gtk_widget_show (self->title_label);

  self->subtitle_label = gtk_label_new ("");
  gtk_style_context_add_class (gtk_widget_get_style_context (self->subtitle_label),
                               "app-cell-subtitle");
  gtk_label_set_line_wrap (GTK_LABEL (self->subtitle_label), TRUE);
  gtk_misc_set_alignment (GTK_MISC (self->subtitle_label), 0.0, 0.5);
  gtk_label_set_max_width_chars (GTK_LABEL (self->subtitle_label), 50);
  gtk_container_add (GTK_CONTAINER (box), self->subtitle_label);
  gtk_widget_show (self->subtitle_label);
}

/*
 * EosAppInfo
 */
struct _EosAppInfo
{
  volatile int ref_count;

  char *desktop_id;

  char *title;
  char *subtitle;
  char *description;

  char *square_img;
  char *featured_img;

  char **screenshots;
  guint n_screenshots;

  EosFlexyShape shape;

  EosAppCategory category;

  guint is_featured : 1;
  guint is_offline  : 1;
};

G_DEFINE_BOXED_TYPE (EosAppInfo, eos_app_info, eos_app_info_ref, eos_app_info_unref)

EosAppInfo *
eos_app_info_new (void)
{
  EosAppInfo *info = g_slice_new0 (EosAppInfo);

  info->shape = EOS_FLEXY_SHAPE_SMALL;
  info->ref_count = 1;

  return info;
}

EosAppInfo *
eos_app_info_ref (EosAppInfo *info)
{
  if (info == NULL)
    return NULL;

  g_atomic_int_inc (&(info->ref_count));

  return info;
}

void
eos_app_info_unref (EosAppInfo *info)
{
  if (info == NULL)
    return;

  if (g_atomic_int_dec_and_test (&(info->ref_count)))
    {
      g_free (info->desktop_id);
      g_free (info->title);
      g_free (info->subtitle);
      g_free (info->description);
      g_free (info->square_img);
      g_free (info->featured_img);
      g_strfreev (info->screenshots);

      g_slice_free (EosAppInfo, info);
    }
}

const char *
eos_app_info_get_title (const EosAppInfo *info)
{
  if (info != NULL)
    return info->title;

  return "";
}

const char *
eos_app_info_get_subtitle (const EosAppInfo *info)
{
  if (info != NULL)
    return info->subtitle;

  return "";
}

const char *
eos_app_info_get_desktop_id (const EosAppInfo *info)
{
  if (info != NULL)
    return info->desktop_id;

  return "";
}

const char *
eos_app_info_get_description (const EosAppInfo *info)
{
  if (info != NULL)
    return info->description;

  return "";
}

gboolean
eos_app_info_is_featured (const EosAppInfo *info)
{
  if (info != NULL)
    return info->is_featured;

  return FALSE;
}

gboolean
eos_app_info_is_offline (const EosAppInfo *info)
{
  if (info != NULL)
    return info->is_offline;

  return FALSE;
}

EosAppCategory
eos_app_info_get_category (const EosAppInfo *info)
{
  if (info != NULL)
    return info->category;

  return EOS_APP_CATEGORY_UTILITIES;
}

static EosFlexyShape
eos_app_info_get_shape_for_cell (const EosAppInfo *info)
{
  /* Everywhere else it's assumed that only
   * featured apps get their large image.
   */
  if (eos_app_info_is_featured (info))
    return info->shape;
  else
    return EOS_FLEXY_SHAPE_SMALL;
}

/**
 * eos_app_info_get_square_img:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_info_get_square_img (const EosAppInfo *info)
{
  char *path, *res;

  if (info == NULL || info->square_img == NULL || info->square_img[0] == '\0')
    return NULL;

  path = eos_app_get_content_dir ();
  res = g_build_filename (path, "resources", "thumbnails", info->square_img, NULL);

  g_free (path);

  return res;
}

/**
 * eos_app_info_get_featured_img:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_info_get_featured_img (const EosAppInfo *info)
{
  char *path, *res;

  if (info == NULL || info->featured_img == NULL || info->featured_img[0] == '\0')
    return NULL;

  path = eos_app_get_content_dir ();
  res = g_build_filename (path, "resources", "images", info->featured_img, NULL);

  g_free (path);

  return res;
}

guint
eos_app_info_get_n_screenshots (const EosAppInfo *info)
{
  if (info == NULL)
    return 0;

  return info->n_screenshots;
}

/**
 * eos_app_info_get_screenshots:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full) (array zero-terminated=1): ...
 */
char **
eos_app_info_get_screenshots (const EosAppInfo *info)
{
  if (info == NULL)
    return NULL;

  return g_strdupv (info->screenshots);
}

/**
 * eos_app_info_create_cell:
 * @info:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
GtkWidget *
eos_app_info_create_cell (const EosAppInfo *info)
{
  if (info == NULL)
    return NULL;

  GtkWidget *res = g_object_new (eos_app_cell_get_type (),
                                 "shape", eos_app_info_get_shape_for_cell (info),
                                 "title", info->title,
                                 "subtitle", info->subtitle,
                                 "desktop-id", info->desktop_id,
                                 "app-info", info,
                                 NULL);

  return res;
}

/* Keep in the same order as the EosAppCategory enumeration */
static const struct {
  const EosAppCategory category;
  const char *id;
} categories[] = {
  /* Translators: use the same string used to install the app store content JSON */
  { EOS_APP_CATEGORY_EDUCATION, N_("Education") },
  { EOS_APP_CATEGORY_LEISURE,   N_("Leisure") },
  { EOS_APP_CATEGORY_UTILITIES, N_("Utilities") },
};

static const guint n_categories = G_N_ELEMENTS (categories);

static EosAppCategory
get_category_from_id (const char *p)
{
  guint i;

  if (p == NULL || *p == '\0')
    return EOS_APP_CATEGORY_UTILITIES;

  for (i = 0; i < n_categories; i++)
    {
      if (strcmp (categories[i].id, p) == 0)
        return categories[i].category;
    }

  return EOS_APP_CATEGORY_UTILITIES;
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

static void
get_screenshots (JsonArray *array,
                 EosAppInfo *info)
{
  info->n_screenshots = json_array_get_length (array);
  info->screenshots = g_new0 (char *, info->n_screenshots + 1);

  char *path = eos_app_get_content_dir ();

  for (guint i = 0; i < info->n_screenshots; i++)
    info->screenshots[i] = g_build_filename (path,
                                             "resources",
                                             "screenshots",
                                             json_array_get_string_element (array, i),
                                             NULL);

  g_free (path);
}

/*< private >*/
EosAppInfo *
eos_app_info_create_from_json (JsonNode *node)
{
  if (!JSON_NODE_HOLDS_OBJECT (node))
    return NULL;

  JsonObject *obj = json_node_get_object (node);

  EosAppInfo *info = eos_app_info_new ();

  if (json_object_has_member (obj, "desktop-id"))
    info->desktop_id = json_node_dup_string (json_object_get_member (obj, "desktop-id"));
  else
    info->desktop_id = NULL;

  if (json_object_has_member (obj, "title"))
    info->title = json_node_dup_string (json_object_get_member (obj, "title"));
  else
    info->title = g_strdup ("");

  if (json_object_has_member (obj, "subtitle"))
    info->subtitle = json_node_dup_string (json_object_get_member (obj, "subtitle"));
  else
    info->subtitle = g_strdup ("");

  if (json_object_has_member (obj, "description"))
    info->description = json_node_dup_string (json_object_get_member (obj, "description"));
  else
    info->description = g_strdup ("");

  if (json_object_has_member (obj, "displayShape"))
    {
      const char *shape = json_object_get_string_member (obj, "displayShape");

      info->shape = get_shape_from_id (shape); 
    }
  else
    info->shape = EOS_FLEXY_SHAPE_SMALL;

  if (json_object_has_member (obj, "square_img"))
    info->square_img = json_node_dup_string (json_object_get_member (obj, "square_img"));
  else
    info->square_img = NULL;

  if (json_object_has_member (obj, "featured_img"))
    info->featured_img = json_node_dup_string (json_object_get_member (obj, "featured_img"));
  else
    info->featured_img = NULL;

  /* FIXME: needs to be a boolean */
  if (json_object_has_member (obj, "is_featured") &&
      json_object_get_boolean_member (obj, "is_featured"))
    info->is_featured = TRUE;
  else
    info->is_featured = FALSE;

  /* FIXME: needs to be a boolean */
  if (json_object_has_member (obj, "is_offline") &&
      json_object_get_boolean_member (obj, "is_offline"))
    info->is_offline = TRUE;
  else
    info->is_offline = FALSE;

  if (json_object_has_member (obj, "category"))
    {
      const char *category = json_object_get_string_member (obj, "category");

      info->category = get_category_from_id (category);
    }
  else
    info->category = EOS_APP_CATEGORY_UTILITIES;

  if (json_object_has_member (obj, "screenshots"))
    {
      JsonNode *node = json_object_get_member (obj, "screenshots");

      if (JSON_NODE_HOLDS_ARRAY (node))
        get_screenshots (json_node_get_array (node), info);
    }
  else
    info->n_screenshots = 0;

  return info;
}
