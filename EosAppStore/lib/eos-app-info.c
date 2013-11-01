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
  PROP_SELECTED,
  PROP_ICON,
  NUM_PROPS
};

struct _EosAppCell {
  EosFlexyGridCell parent;

  char *desktop_id;
  char *icon_name;

  GtkWidget *title_label;
  GtkWidget *subtitle_label;
  GtkWidget *icon;
  GtkWidget *icon_hbox;

  EosAppInfo *info;

  GdkPixbuf *image;
  GdkPixbuf *selected_image;
  GtkStyleContext *image_context;

  gint cell_margin;

  guint is_selected : 1;
};

struct _EosAppCellClass {
  EosFlexyGridCellClass parent_class;
};

static GParamSpec *eos_app_cell_props[NUM_PROPS] = { NULL, };

G_DEFINE_TYPE (EosAppCell, eos_app_cell, EOS_TYPE_FLEXY_GRID_CELL)

#define PROVIDER_DATA_FORMAT ".app-cell-image { " \
  "background-image: url(\"%s\"); "               \
  "background-size: 100%% 100%%; }"

static GtkStyleContext *
eos_app_info_get_cell_style_context (void)
{
  GtkStyleContext *style_context;
  GtkWidgetPath *widget_path;

  widget_path = gtk_widget_path_new ();
  gtk_widget_path_append_type (widget_path, eos_app_cell_get_type ());

  style_context = gtk_style_context_new ();
  gtk_style_context_set_path (style_context, widget_path);
  gtk_style_context_add_class (style_context, "app-cell-image");
  gtk_widget_path_free (widget_path);

  return style_context;
}

static gint
eos_app_info_get_cell_margin_for_context (GtkStyleContext *context)
{
  GtkBorder margin, select_margin;
  gint retval;

  gtk_style_context_get_margin (context,
                                GTK_STATE_FLAG_NORMAL,
                                &margin);

  gtk_style_context_save (context);
  gtk_style_context_add_class (context, "select");
  gtk_style_context_get_margin (context,
                                GTK_STATE_FLAG_NORMAL,
                                &select_margin);
  gtk_style_context_restore (context);

  margin.top = MAX (margin.top, select_margin.top);
  margin.right = MAX (margin.right, select_margin.right);
  margin.bottom = MAX (margin.bottom, select_margin.bottom);
  margin.left = MAX (margin.left, select_margin.left);

  retval = margin.top + margin.bottom;
  retval = MAX (retval, margin.left + margin.right);

  return retval;
}

static GdkPixbuf *
prepare_pixbuf_from_file (EosAppCell *self,
                          const gchar *path,
                          gint image_width,
                          gint image_height,
                          GError **error)
{
  GdkPixbuf *retval;
  cairo_surface_t *surface;
  cairo_t *cr;
  GtkCssProvider *provider;
  gchar *provider_data;

  provider_data = g_strdup_printf (PROVIDER_DATA_FORMAT, path);
  provider = gtk_css_provider_new ();

  if (!gtk_css_provider_load_from_data (provider, provider_data, -1, error))
    {
      g_free (provider_data);
      g_object_unref (provider);

      return NULL;
    }

  gtk_style_context_add_provider (self->image_context,
                                  GTK_STYLE_PROVIDER (provider),
                                  GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

  surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                        image_width, image_height);
  cr = cairo_create (surface);
  gtk_render_background (self->image_context, cr,
                         0, 0, image_width, image_height);

  retval = gdk_pixbuf_get_from_surface (surface, 0, 0,
                                        image_width, image_height);

  cairo_destroy (cr);
  cairo_surface_destroy (surface);
  gtk_style_context_remove_provider (self->image_context,
                                     GTK_STYLE_PROVIDER (provider));

  g_free (provider_data);
  g_object_unref (provider);

  return retval;
}

static GdkPixbuf *
prepare_selected_pixbuf (EosAppCell *self,
                         gint image_width,
                         gint image_height)
{
  GdkPixbuf *retval;
  cairo_surface_t *surface;
  cairo_t *cr;

  surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                        image_width, image_height);
  cr = cairo_create (surface);
  gtk_render_background (self->image_context, cr,
                         0, 0, image_width, image_height);
  gtk_render_frame (self->image_context, cr,
                    0, 0, image_width, image_height);

  retval = gdk_pixbuf_get_from_surface (surface, 0, 0,
                                        image_width, image_height);

  cairo_destroy (cr);
  cairo_surface_destroy (surface);

  return retval;
}

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

    case PROP_SELECTED:
      g_value_set_boolean (value, self->is_selected);
      break;

    case PROP_ICON:
      g_value_set_string (value, self->icon_name);
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

    case PROP_SELECTED:
      {
        GtkStyleContext *context = gtk_widget_get_style_context (GTK_WIDGET (self));

        self->is_selected = g_value_get_boolean (value);
        if (self->is_selected)
          gtk_style_context_add_class (context, "select");
        else
          gtk_style_context_remove_class (context, "select");
      }
      break;

    case PROP_ICON:
      {
        const char *icon_name = g_value_get_string (value);

        g_free (self->icon_name);
        self->icon_name = g_strdup (icon_name);

        if (icon_name == NULL)
          {
            gtk_image_clear (GTK_IMAGE (self->icon));
            gtk_widget_hide (self->icon_hbox);
          }
        else
          {
            gtk_image_set_from_icon_name (GTK_IMAGE (self->icon),
                                          icon_name,
                                          GTK_ICON_SIZE_DIALOG);
            gtk_widget_show (self->icon_hbox);
          }
      }
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_app_cell_finalize (GObject *gobject)
{
  EosAppCell *self = (EosAppCell *) gobject;

  g_clear_object (&self->image_context);
  g_clear_object (&self->image);
  g_clear_object (&self->selected_image);
  g_free (self->desktop_id);
  g_free (self->icon_name);
  eos_app_info_unref (self->info);

  G_OBJECT_CLASS (eos_app_cell_parent_class)->finalize (gobject);
}

static void
eos_app_cell_draw_selected (EosAppCell *self,
                            cairo_t *cr,
                            gint width,
                            gint height)
{
  gint image_width, image_height;
  GtkBorder image_margin;

  gtk_style_context_save (self->image_context);
  gtk_style_context_add_class (self->image_context, "select");

  if (self->selected_image != NULL)
    goto out;

  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;

  self->selected_image = prepare_selected_pixbuf (self, image_width, image_height);

 out:
  gtk_style_context_get_margin (self->image_context,
                                GTK_STATE_FLAG_NORMAL,
                                &image_margin);
  gtk_render_icon (self->image_context,
                   cr,
                   self->selected_image,
                   MAX (image_margin.top, (gint) self->cell_margin / 2),
                   MAX (image_margin.left, (gint) self->cell_margin / 2));
  gtk_style_context_restore (self->image_context);
}

static void
eos_app_cell_draw_normal (EosAppCell *self,
                          cairo_t *cr,
                          gint width,
                          gint height)
{
  gchar *path;
  GError *error;
  gint image_width, image_height;
  GtkBorder image_margin;
  EosFlexyShape shape;

  if (self->image != NULL)
    goto out;

  path = NULL;
  shape = eos_flexy_grid_cell_get_shape (EOS_FLEXY_GRID_CELL (self));

  if (shape != EOS_FLEXY_SHAPE_SMALL)
    path = eos_app_info_get_featured_img (self->info);

  /* If featured image not available, or not featured */
  if (path == NULL)
    path = eos_app_info_get_square_img (self->info);

  /* If neither featured image nor square image available */
  if (path == NULL)
    {
      g_warning ("No image found for app info '%s'[%p]",
                 eos_app_info_get_title (self->info),
                 self->info);
      goto out;
    }

  error = NULL;
  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;

  self->image = prepare_pixbuf_from_file (self, path, image_width, image_height, &error);

  if (error != NULL)
    {
      g_warning ("Unable to load image at path '%s': %s",
                 path, error->message);
      g_error_free (error);
    }

  g_free (path);

out:
  if (self->image != NULL)
    {
      gtk_style_context_get_margin (self->image_context,
                                    GTK_STATE_FLAG_NORMAL,
                                    &image_margin);

      gtk_render_icon (self->image_context,
                       cr,
                       self->image,
                       MAX (image_margin.top, (gint) self->cell_margin / 2),
                       MAX (image_margin.left, (gint) self->cell_margin / 2));
    }
}

static gboolean
eos_app_cell_draw (GtkWidget *widget,
                   cairo_t   *cr)
{
  EosAppCell *self = (EosAppCell *) widget;
  GtkAllocation allocation;
  int width, height;

  if (self->info == NULL)
    {
      g_critical ("No EosAppInfo found for cell %p", widget);
      return FALSE;
    }

  gtk_widget_get_allocation (widget, &allocation);
  width = allocation.width;
  height = allocation.height;

  if (self->is_selected)
    eos_app_cell_draw_selected (self, cr,
                                width, height);
  else
    eos_app_cell_draw_normal (self, cr,
                              width, height);

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

  eos_app_cell_props[PROP_SELECTED] =
    g_param_spec_boolean ("selected",
                          "Selected",
                          "Whether the cell is selected",
                          FALSE,
                          G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

  eos_app_cell_props[PROP_ICON] =
    g_param_spec_string ("icon",
                         "Icon",
                         "Icon name of the app",
                         NULL,
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

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

  GtkWidget *hbox = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 13);
  self->icon_hbox = hbox;
  gtk_widget_set_hexpand (hbox, TRUE);
  gtk_container_add (GTK_CONTAINER (box), hbox);
  gtk_widget_set_no_show_all (hbox, TRUE);

  self->icon = gtk_image_new ();
  gtk_widget_show (self->icon);
  gtk_style_context_add_class (gtk_widget_get_style_context (self->icon),
                               "app-cell-icon");
  gtk_widget_set_halign (self->icon, GTK_ALIGN_START);
  gtk_container_add (GTK_CONTAINER (hbox), self->icon);

  GtkWidget *arrow = gtk_image_new_from_resource ("/com/endlessm/appstore/icon_arrow_thumb.png");
  gtk_widget_show (arrow);
  gtk_widget_set_valign (arrow, GTK_ALIGN_CENTER);
  gtk_container_add (GTK_CONTAINER (hbox), arrow);

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

  self->image_context = eos_app_info_get_cell_style_context ();
  self->cell_margin = eos_app_info_get_cell_margin_for_context (self->image_context);
}

gint
eos_app_info_get_cell_margin (void)
{
  GtkStyleContext *context;
  gint retval;

  context = eos_app_info_get_cell_style_context ();
  retval = eos_app_info_get_cell_margin_for_context (context);
  g_object_unref (context);

  return retval;
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
    return g_dpgettext2 (GETTEXT_PACKAGE, "title", info->title);

  return "";
}

const char *
eos_app_info_get_subtitle (const EosAppInfo *info)
{
  if (info != NULL)
    return g_dpgettext2 (GETTEXT_PACKAGE, "subtitle", info->subtitle);

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
    return g_dpgettext2 (GETTEXT_PACKAGE, "description", info->description);

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
  if (info == NULL || info->square_img == NULL || info->square_img[0] == '\0')
    return NULL;

  return g_strdup_printf ("resource:///com/endlessm/appstore/apps/%s/%s",
                          eos_get_system_personality (),
                          info->featured_img);
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
  if (info == NULL || info->featured_img == NULL || info->featured_img[0] == '\0')
    return NULL;

  return g_strdup_printf ("resource:///com/endlessm/appstore/apps/%s/%s",
                          eos_get_system_personality (),
                          info->featured_img);
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
 * Returns: (transfer full) (type EosAppCell): ...
 */
GtkWidget *
eos_app_info_create_cell (const EosAppInfo *info)
{
  if (info == NULL)
    return NULL;

  GtkWidget *res = g_object_new (eos_app_cell_get_type (),
                                 "shape", eos_app_info_get_shape_for_cell (info),
                                 "title", eos_app_info_get_title (info),
                                 "subtitle", eos_app_info_get_subtitle (info),
                                 "desktop-id", info->desktop_id,
                                 "app-info", info,
                                 NULL);

  g_object_ref_sink (res);

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
