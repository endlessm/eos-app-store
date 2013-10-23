#include "config.h"

#include "eos-link-info.h"
#include "eos-app-utils.h"

#include <gdk-pixbuf/gdk-pixbuf.h>

#define SELECTED (GTK_STATE_FLAG_ACTIVE | GTK_STATE_FLAG_PRELIGHT | GTK_STATE_FLAG_SELECTED)

struct _EosLinkRow {
  GtkBin parent;

  EosLinkInfo *link_info;

  GdkPixbuf *bg_image_normal;
  GdkPixbuf *bg_image_selected;
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

static GdkPixbuf *
get_pixbuf_background (EosLinkRow *self,
                       gint image_width,
                       gint image_height)
{
  GdkPixbuf *retval;
  cairo_surface_t *surface;
  cairo_t *cr;
  GtkStyleContext *context = gtk_widget_get_style_context (GTK_WIDGET(self));

  surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                        image_width, image_height);
  cr = cairo_create (surface);
  gtk_render_background (context, cr,
                         0, 0, image_width, image_height);
  gtk_render_frame (context, cr,
                    0, 0, image_width, image_height);

  retval = gdk_pixbuf_get_from_surface (surface, 0, 0,
                                        image_width, image_height);

  cairo_destroy (cr);
  cairo_surface_destroy (surface);

  return retval;
}

static gboolean
eos_link_row_draw (GtkWidget *widget,
                   cairo_t   *cr)
{
  EosLinkRow *self = (EosLinkRow *) widget;

  GtkAllocation allocation;
  GdkPixbuf *background;
  GtkBorder margin;
  int image_width, image_height;

  GtkStyleContext *context = gtk_widget_get_style_context (widget);
  gtk_style_context_get_margin (context,
                                gtk_style_context_get_state (context),
                                &margin);

  gtk_widget_get_allocation (widget, &allocation);

  image_width = allocation.width - margin.left - margin.right;
  image_height = allocation.height - margin.top - margin.bottom;

  if (gtk_widget_get_state_flags (widget) & SELECTED)
    {
      if (!self->bg_image_selected)
        self->bg_image_selected = get_pixbuf_background (self, image_width, image_height);
      background = self->bg_image_selected;
    }
  else
    {
      if (!self->bg_image_normal)
        self->bg_image_normal = get_pixbuf_background (self, image_width, image_height);
      background = self->bg_image_normal;
  }

  gtk_render_icon (context,
                   cr,
                   background,
                   margin.top,
                   margin.left);

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->draw (widget, cr);

  return FALSE;
}

static void
eos_link_row_get_preferred_width (GtkWidget *widget,
                                      gint      *minimum_width,
                                      gint      *natural_width)
{
  GtkBorder margin;
  GtkStyleContext *context = gtk_widget_get_style_context (widget);

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->get_preferred_width (widget, minimum_width, natural_width);

  gtk_style_context_get_margin (context,
                                gtk_style_context_get_state (context),
                                &margin);

  if (minimum_width)
    *minimum_width += margin.left + margin.right;
  if (natural_width)
    *natural_width += margin.left + margin.right;
}

static void
eos_link_row_get_preferred_height (GtkWidget *widget,
                                       gint      *minimum_height,
                                       gint      *natural_height)
{
  GtkBorder margin;
  GtkStyleContext *context = gtk_widget_get_style_context (widget);

  GTK_WIDGET_CLASS (eos_link_row_parent_class)->get_preferred_height (widget, minimum_height, natural_height);

  gtk_style_context_get_margin (context,
                                gtk_style_context_get_state (context),
                                &margin);

  if (minimum_height)
    *minimum_height += margin.top + margin.bottom;
  if (natural_height)
    *natural_height += margin.top + margin.bottom;
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
      self->link_info = eos_link_info_ref (g_value_get_boxed (value));
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

  g_clear_object (&self->bg_image_normal);
  g_clear_object (&self->bg_image_selected);

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
  GtkStyleContext *context;

  context = gtk_widget_get_style_context (GTK_WIDGET (self));
  gtk_style_context_add_class (context, "weblink-row");
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
      g_clear_object (&(info->thumbnail));
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

/**
 * eos_link_info_get_thumbnail:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer none): ...
 */
GdkPixbuf *
eos_link_info_get_thumbnail (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->thumbnail;
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
  gchar *thumbnail_filename;
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
      thumbnail_filename = g_build_filename (path,
                                             json_node_get_string (json_object_get_member (obj, "linkSmall")),
                                             NULL);
      info->thumbnail = gdk_pixbuf_new_from_file (thumbnail_filename, NULL);
      g_free (path);
      if (info->thumbnail)
        {
          info->thumbnail_filename = thumbnail_filename;
        }
      else
        {
          info->thumbnail_filename = NULL;
          g_free (thumbnail_filename);
        }
    }
  else
    {
      info->thumbnail = NULL;
      info->thumbnail_filename = NULL;
    }

  if (json_object_has_member (obj, "linkUrl"))
    info->url = json_node_dup_string (json_object_get_member (obj, "linkUrl"));
  else
    info->url = g_strdup ("");

  return info;
}
