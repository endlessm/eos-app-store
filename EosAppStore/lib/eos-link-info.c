#include "config.h"

#include "eos-link-info.h"
#include "eos-app-utils.h"

#include <gdk-pixbuf/gdk-pixbuf.h>

#define SELECTED (GTK_STATE_FLAG_ACTIVE | GTK_STATE_FLAG_PRELIGHT | GTK_STATE_FLAG_SELECTED)

struct _EosLinkRow {
  GtkBin parent;

  EosLinkInfo *link_info;

  GdkPixbuf *image;
  GdkPixbuf *selected_image;

  GtkStyleContext *image_context;

  gint cell_margin;
};

struct _EosLinkRowClass {
  GtkBinClass parent_class;
};

enum {
  PROP_0,
  PROP_LINK_INFO,
  NUM_PROPS
};

static GParamSpec * eos_link_row_props[NUM_PROPS] = { NULL, };

G_DEFINE_TYPE (EosLinkRow, eos_link_row, GTK_TYPE_BIN)

#define PROVIDER_DATA_FORMAT ".weblink-row-image { " \
  "background-image: url(\"%s\"); "                  \
  "background-repeat: no-repeat; "                   \
  "background-size: 90px 90px; }"

static GtkStyleContext *
eos_link_row_get_cell_style_context (void)
{
  GtkStyleContext *style_context;
  GtkWidgetPath *widget_path;

  widget_path = gtk_widget_path_new ();
  gtk_widget_path_append_type (widget_path, eos_link_row_get_type ());

  style_context = gtk_style_context_new ();
  gtk_style_context_set_path (style_context, widget_path);
  gtk_style_context_add_class (style_context, "weblink-row-image");
  gtk_widget_path_free (widget_path);

  return style_context;
}

static gint
eos_link_row_get_cell_margin_for_context (GtkStyleContext *context)
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
get_selected_pixbuf_background (EosLinkRow *self,
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

static GdkPixbuf *
get_pixbuf_background (EosLinkRow *self,
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

static void
eos_link_row_draw_selected (EosLinkRow *self,
                            cairo_t *cr,
                            gint width,
                            gint height)
{
  gint image_width, image_height;
  GtkBorder image_margin;

  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;

  gtk_style_context_save (self->image_context);
  gtk_style_context_add_class (self->image_context, "select");

  if (self->selected_image == NULL)
    self->selected_image = get_selected_pixbuf_background (self, image_width, image_height);

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
eos_link_row_draw_normal (EosLinkRow *self,
                          cairo_t *cr,
                          gint width,
                          gint height)
{
  gint image_width, image_height;
  GtkBorder image_margin;

  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;

  if (self->image == NULL)
    self->image = get_pixbuf_background (self,
                                         eos_link_info_get_thumbnail_filename (self->link_info),
                                         image_width, image_height, NULL);

  gtk_style_context_get_margin (self->image_context,
                                GTK_STATE_FLAG_NORMAL,
                                &image_margin);

  gtk_render_icon (self->image_context,
                   cr,
                   self->image,
                   MAX (image_margin.top, (gint) self->cell_margin / 2),
                   MAX (image_margin.left, (gint) self->cell_margin / 2));
}

static gboolean
eos_link_row_draw (GtkWidget *widget,
                   cairo_t   *cr)
{
  EosLinkRow *self = (EosLinkRow *) widget;
  gint width, height;

  width = gtk_widget_get_allocated_width (widget);
  height = gtk_widget_get_allocated_height (widget);

  if (gtk_widget_get_state_flags (widget) & SELECTED)
    eos_link_row_draw_selected (self, cr, width, height);
  else
    eos_link_row_draw_normal (self, cr, width, height);

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->draw (widget, cr);

  return FALSE;
}

static void
eos_link_row_get_preferred_width (GtkWidget *widget,
                                  gint      *minimum_width,
                                  gint      *natural_width)
{
  EosLinkRow *self = (EosLinkRow *) widget;

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->get_preferred_width (widget, minimum_width, natural_width);

  if (minimum_width)
    *minimum_width += self->cell_margin;
  if (natural_width)
    *natural_width += self->cell_margin;
}

static void
eos_link_row_get_preferred_height (GtkWidget *widget,
                                   gint      *minimum_height,
                                   gint      *natural_height)
{
  EosLinkRow *self = (EosLinkRow *) widget;

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->get_preferred_height (widget, minimum_height, natural_height);

  if (minimum_height)
    *minimum_height += self->cell_margin;
  if (natural_height)
    *natural_height += self->cell_margin;
}

static void
eos_link_row_get_property (GObject    *gobject,
                           guint       prop_id,
                           GValue     *value,
                           GParamSpec *pspec)
{
  EosLinkRow *self = (EosLinkRow *) gobject;

  switch (prop_id)
    {
    case PROP_LINK_INFO:
      g_value_set_boxed (value, self->link_info);
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_link_row_set_property (GObject      *gobject,
                           guint         prop_id,
                           const GValue *value,
                           GParamSpec   *pspec)
{
  EosLinkRow *self = (EosLinkRow *) gobject;

  switch (prop_id)
    {
    case PROP_LINK_INFO:
      g_assert (self->link_info == NULL);
      self->link_info = g_value_dup_boxed (value);
      g_assert (self->link_info != NULL);
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_link_row_finalize (GObject *gobject)
{
  EosLinkRow *self = (EosLinkRow *) gobject;

  g_clear_object (&self->image);
  g_clear_object (&self->selected_image);
  g_clear_object (&self->image_context);

  g_clear_pointer (&self->link_info, eos_link_info_unref);

  G_OBJECT_CLASS (eos_link_row_parent_class)->finalize (gobject);
}

static void
eos_link_row_class_init (EosLinkRowClass *klass)
{
  GObjectClass *oclass = G_OBJECT_CLASS (klass);
  GtkWidgetClass *wclass = GTK_WIDGET_CLASS (klass);

  oclass->finalize = eos_link_row_finalize;
  oclass->get_property = eos_link_row_get_property;
  oclass->set_property = eos_link_row_set_property;

  wclass->draw = eos_link_row_draw;
  wclass->get_preferred_width = eos_link_row_get_preferred_width;
  wclass->get_preferred_height = eos_link_row_get_preferred_height;

  eos_link_row_props[PROP_LINK_INFO] =
    g_param_spec_boxed ("link-info",
                        "Link Info",
                        "Link Info",
                        EOS_TYPE_LINK_INFO,
                        G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS | G_PARAM_CONSTRUCT_ONLY);

  g_object_class_install_properties (oclass, NUM_PROPS, eos_link_row_props);
}

static void
eos_link_row_init (EosLinkRow *self)
{
  self->image_context = eos_link_row_get_cell_style_context ();
  self->cell_margin = eos_link_row_get_cell_margin_for_context (self->image_context);
}

struct _EosLinkInfo
{
  volatile int ref_count;

  gchar *id;
  gchar *title;
  gchar *description;
  gchar *icon_filename;
  gchar *thumbnail_filename;
  GdkPixbuf *icon;
  GdkPixbuf *thumbnail;
  gchar *url;
};

G_DEFINE_BOXED_TYPE (EosLinkInfo, eos_link_info, eos_link_info_ref, eos_link_info_unref)

EosLinkInfo *
eos_link_info_new (void)
{
  EosLinkInfo *info = g_slice_new (EosLinkInfo);

  info->ref_count = 1;

  return info;
}

EosLinkInfo *
eos_link_info_ref (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  g_atomic_int_inc (&(info->ref_count));

  return info;
}

void
eos_link_info_unref (EosLinkInfo *info)
{
  g_return_if_fail (info != NULL);

  if (g_atomic_int_dec_and_test (&(info->ref_count)))
    {
      g_free (info->id);
      g_free (info->title);
      g_free (info->description);
      g_free (info->icon_filename);
      g_free (info->thumbnail_filename);
      g_clear_object (&(info->icon));
      g_free (info->url);

      g_slice_free (EosLinkInfo, info);
    }
}

const gchar *
eos_link_info_get_id (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->id;
}

const gchar *
eos_link_info_get_title (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->title;
}

const gchar *
eos_link_info_get_description (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->description;
}

const gchar *
eos_link_info_get_icon_filename (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->icon_filename;
}

const gchar *
eos_link_info_get_thumbnail_filename (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->thumbnail_filename;
}

/**
 * eos_link_info_get_icon:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer none): ...
 */
GdkPixbuf *
eos_link_info_get_icon (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->icon;
}

const gchar *
eos_link_info_get_url (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->url;
}

/**
 * eos_link_info_create_row:
 *
 * Returns: (transfer none): a pointer to the newly-created widget.
 */
GtkWidget *
eos_link_info_create_row (EosLinkInfo *info)
{
  return g_object_new (eos_link_row_get_type (),
                       "link-info", info,
                       NULL);
}

/*< private >*/
EosLinkInfo *
eos_link_info_create_from_json (JsonNode *node)
{
  EosLinkInfo *info;
  JsonObject *obj;
  gchar *path;
  gchar *icon_filename;

  g_return_val_if_fail (JSON_NODE_HOLDS_OBJECT (node), NULL);

  obj = json_node_get_object (node);
  info = eos_link_info_new ();

  if (json_object_has_member (obj, "linkId"))
    info->id = json_node_dup_string (json_object_get_member (obj, "linkId"));
  else
    info->id = NULL;

  if (json_object_has_member (obj, "linkName"))
    info->title = json_node_dup_string (json_object_get_member (obj, "linkName"));
  else
    info->title = g_strdup ("");

  if (json_object_has_member (obj, "linkSubtitle"))
    info->description = json_node_dup_string (json_object_get_member (obj, "linkSubtitle"));
  else
    info->description = g_strdup ("");
  
  if (json_object_has_member (obj, "linkIcon"))
    {
      path = eos_link_get_content_dir();
      icon_filename = g_build_filename (path,
                                        json_node_get_string (json_object_get_member (obj, "linkIcon")),
                                        NULL);
      info->icon = gdk_pixbuf_new_from_file (icon_filename, NULL);
      g_free (path);
      if (info->icon)
        {
          info->icon_filename = icon_filename;
        }
      else
        {
          info->icon_filename = NULL;
          g_free (icon_filename);
        }
    }
  else
    {
      info->icon = NULL;
      info->icon_filename = NULL;
    }

  if (json_object_has_member (obj, "linkSmall"))
    {
      path = eos_link_get_content_dir();
      info->thumbnail_filename = g_build_filename (path,
                                             json_node_get_string (json_object_get_member (obj, "linkSmall")),
                                             NULL);
    }
  else
    {
      info->thumbnail_filename = NULL;
    }

  if (json_object_has_member (obj, "linkUrl"))
    info->url = json_node_dup_string (json_object_get_member (obj, "linkUrl"));
  else
    info->url = g_strdup ("");

  return info;
}
