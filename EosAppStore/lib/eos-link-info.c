#include "config.h"

#include "eos-link-info.h"
#include "eos-app-utils.h"

#include <gdk-pixbuf/gdk-pixbuf.h>

struct _EosLinkRow {
  GtkListBoxRow parent;

  EosLinkInfo *link_info;

  cairo_surface_t *image;
  cairo_surface_t *icon;

  gboolean show_icon;

  GtkStyleContext *image_context;

  gint cell_margin;
};

struct _EosLinkRowClass {
  GtkListBoxRowClass parent_class;
};

enum {
  PROP_0,
  PROP_LINK_INFO,
  PROP_SHOW_ICON,
  NUM_PROPS
};

static GParamSpec * eos_link_row_props[NUM_PROPS] = { NULL, };

G_DEFINE_TYPE (EosLinkRow, eos_link_row, GTK_TYPE_LIST_BOX_ROW)

#define DEFAULT_LINK_ICON_NAME "generic-link"

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
  GtkBorder margin;
  gint retval;

  gtk_style_context_get_margin (context,
                                GTK_STATE_FLAG_NORMAL,
                                &margin);

  retval = margin.top + margin.bottom;
  retval = MAX (retval, margin.left + margin.right);

  return retval;
}

static cairo_surface_t *
get_icon_surface_background (EosLinkRow *self,
                             gint image_width,
                             gint image_height)
{
  cairo_surface_t *surface;
  cairo_t *cr;

  surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                        image_width, image_height);
  cr = cairo_create (surface);
  gtk_render_background (self->image_context, cr,
                         0, 0, image_width, image_height);
  gtk_render_frame (self->image_context, cr,
                    0, 0, image_width, image_height);

  cairo_destroy (cr);

  return surface;
}

static cairo_surface_t *
get_thumbnail_surface_background (EosLinkRow *self,
                                  const gchar *path,
                                  gint image_width,
                                  gint image_height,
                                  GError **error)
{
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

  cairo_destroy (cr);
  gtk_style_context_remove_provider (self->image_context,
                                     GTK_STYLE_PROVIDER (provider));

  g_free (provider_data);
  g_object_unref (provider);

  return surface;
}

static void
eos_link_row_draw_with_icon (EosLinkRow *self,
                             cairo_t *cr,
                             gint width,
                             gint height)
{
  gint image_width, image_height;
  GtkBorder image_margin;

  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;

  gtk_style_context_save (self->image_context);

  if (self->icon == NULL)
    self->icon = get_icon_surface_background (self, image_width, image_height);

  gtk_style_context_get_margin (self->image_context,
                                GTK_STATE_FLAG_NORMAL,
                                &image_margin);

  gtk_render_icon_surface (self->image_context,
                           cr,
                           self->icon,
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
    self->image = get_thumbnail_surface_background (self,
                                                    eos_link_info_get_thumbnail_filename (self->link_info),
                                                    image_width, image_height, NULL);

  gtk_style_context_get_margin (self->image_context,
                                GTK_STATE_FLAG_NORMAL,
                                &image_margin);

  gtk_render_icon_surface (self->image_context,
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

  if (self->show_icon)
    eos_link_row_draw_with_icon (self, cr, width, height);
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

    case PROP_SHOW_ICON:
      g_value_set_boolean (value, self->show_icon);
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

    case PROP_SHOW_ICON:
      self->show_icon = g_value_get_boolean (value);
      gtk_widget_queue_draw (GTK_WIDGET (self));
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_link_row_finalize (GObject *gobject)
{
  EosLinkRow *self = (EosLinkRow *) gobject;

  g_clear_pointer (&self->image, (GDestroyNotify) cairo_surface_destroy);
  g_clear_pointer (&self->icon, (GDestroyNotify) cairo_surface_destroy);
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

  eos_link_row_props[PROP_SHOW_ICON] =
    g_param_spec_boolean ("show-icon",
                          "Show Icon",
                          "Whether to show the icon associated to the link",
                          FALSE,
                          G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS);

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
  gchar *desktop_id;
  gchar *title;
  gchar *description;
  gchar *thumbnail_filename;
  gchar *icon_name;
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
      g_free (info->desktop_id);
      g_free (info->title);
      g_free (info->description);
      g_free (info->icon_name);
      g_free (info->thumbnail_filename);
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
eos_link_info_get_desktop_id (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->desktop_id;
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
eos_link_info_get_icon_name (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->icon_name;
}

const gchar *
eos_link_info_get_thumbnail_filename (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->thumbnail_filename;
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

  g_return_val_if_fail (JSON_NODE_HOLDS_OBJECT (node), NULL);

  obj = json_node_get_object (node);
  info = eos_link_info_new ();

  if (json_object_has_member (obj, "linkId"))
    info->id = json_node_dup_string (json_object_get_member (obj, "linkId"));
  else
    info->id = NULL;

  if (info->id != NULL)
    info->desktop_id = g_strdup_printf ("eos-link-%s.desktop", info->id);
  else
    info->desktop_id = NULL;

  if (info->id != NULL)
    info->icon_name = g_strdup_printf ("eos-link-%s", info->id);
  else
    info->icon_name = DEFAULT_LINK_ICON_NAME;

  if (json_object_has_member (obj, "linkName"))
    info->title = json_node_dup_string (json_object_get_member (obj, "linkName"));
  else
    info->title = g_strdup ("");

  if (json_object_has_member (obj, "linkSubtitle"))
    info->description = json_node_dup_string (json_object_get_member (obj, "linkSubtitle"));
  else
    info->description = g_strdup ("");  

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
