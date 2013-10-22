#include "config.h"

#include "eos-shadow-frame.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#define _EOS_STYLE_CLASS_SHADOW_FRAME "shadow-frame"

#define EOS_SHADOW_FRAME_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), EOS_TYPE_SHADOW_FRAME, EosShadowFramePrivate))

struct _EosShadowFramePrivate {
  GdkPixbuf *bg_image_normal;
  GdkPixbuf *bg_image_selected;
  guint is_selected : 1;
};

G_DEFINE_TYPE (EosShadowFrame, eos_shadow_frame, GTK_TYPE_BIN)

static GdkPixbuf *
get_pixbuf_background (EosShadowFrame *self,
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
eos_shadow_frame_draw (GtkWidget *widget,
                       cairo_t   *cr)
{
  EosShadowFrame *self = EOS_SHADOW_FRAME (widget);
  EosShadowFramePrivate *priv = self->priv;

  GtkAllocation allocation;
  GdkPixbuf *background;
  GtkBorder margin;
  int image_width, image_height;

  GtkStyleContext *context = gtk_widget_get_style_context (widget);
  gtk_style_context_get_margin(context,
                               gtk_style_context_get_state (context),
                               &margin);

  gtk_widget_get_allocation (widget, &allocation);

  image_width = allocation.width - margin.left - margin.right;
  image_height = allocation.height - margin.top - margin.bottom;

  if (priv->is_selected) {
      if (!priv->bg_image_selected) {
          priv->bg_image_selected = get_pixbuf_background(self, image_width, image_height);
      }
      background = priv->bg_image_selected;
  }
  else {
      if (!priv->bg_image_normal) {
          priv->bg_image_normal = get_pixbuf_background(self, image_width, image_height);
      }
      background = priv->bg_image_normal;
  }

  gtk_render_icon (context,
                   cr,
                   background,
                   margin.top,
                   margin.left);

  GTK_WIDGET_CLASS (eos_shadow_frame_parent_class)->draw (widget, cr);

  return FALSE;
}

static void
eos_shadow_frame_finalize (GObject *gobject)
{
  EosShadowFrame *self = EOS_SHADOW_FRAME (gobject);
  EosShadowFramePrivate *priv = self->priv;

  g_clear_object (&priv->bg_image_normal);
  g_clear_object (&priv->bg_image_selected);

  G_OBJECT_CLASS (eos_shadow_frame_parent_class)->finalize (gobject);
}

static void
eos_shadow_frame_class_init (EosShadowFrameClass *klass)
{
  GObjectClass *oclass = G_OBJECT_CLASS (klass);
  GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

  g_type_class_add_private (klass, sizeof (EosShadowFramePrivate));

  oclass->finalize = eos_shadow_frame_finalize;

  widget_class->draw = eos_shadow_frame_draw;
}

static void
eos_shadow_frame_init (EosShadowFrame *self)
{
  GtkStyleContext *context;

  self->priv = EOS_SHADOW_FRAME_PRIVATE (self);

  context = gtk_widget_get_style_context (GTK_WIDGET (self));
  gtk_style_context_add_class (context, _EOS_STYLE_CLASS_SHADOW_FRAME);
}

/**
 * eos_shadow_frame_new:
 *
 * Returns: a pointer to the newly-created widget.
 */
GtkWidget *
eos_shadow_frame_new ()
{
  return g_object_new (EOS_TYPE_SHADOW_FRAME, NULL);
}
