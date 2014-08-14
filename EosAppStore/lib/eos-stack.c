/* Copyright 2014 Endless Mobile, Inc. */

#include "eos-stack.h"

#include <gtk/gtk.h>

/*
 * EosStack
 *
 * EosStack is the same as a GtkStack except
 * that it can display a white overlay when
 * specific children are visible. While
 * transitioning between children, this
 * overlay fades in/out.
 *
 */

typedef enum {
  EOS_STACK_OVERLAY_TRANSITION_TYPE_NONE,
  EOS_STACK_OVERLAY_TRANSITION_TYPE_VISIBLE,
  EOS_STACK_OVERLAY_TRANSITION_TYPE_SHOW,
  EOS_STACK_OVERLAY_TRANSITION_TYPE_HIDE
} EosStackOverlayTransitionType;

typedef struct {
  gdouble transition_pos;
  guint tick_id;
  gint64 start_time;
  gint64 end_time;

  EosStackOverlayTransitionType overlay_type;
  gboolean show_overlay;
} EosStackPrivate;

G_DEFINE_TYPE_WITH_PRIVATE (EosStack, eos_stack, GTK_TYPE_STACK)

static gboolean
eos_stack_draw (GtkWidget *widget,
		cairo_t   *cr)
{
  EosStack *stack = EOS_STACK (widget);
  EosStackPrivate *priv = eos_stack_get_instance_private (stack);

  GtkAllocation allocation;
  gtk_widget_get_allocation (widget, &allocation);

  gdouble overlay_opacity;
  switch (priv->overlay_type)
    {
    case EOS_STACK_OVERLAY_TRANSITION_TYPE_NONE:
      overlay_opacity = 0.0;
      break;
    case EOS_STACK_OVERLAY_TRANSITION_TYPE_VISIBLE:
      overlay_opacity = 1.0;
      break;
    case EOS_STACK_OVERLAY_TRANSITION_TYPE_SHOW:
      overlay_opacity = priv->transition_pos;
      break;
    case EOS_STACK_OVERLAY_TRANSITION_TYPE_HIDE:
      overlay_opacity = 1 - priv->transition_pos;
      break;
    default:
      overlay_opacity = 0.0;
    }

  GtkStyleContext *context = gtk_widget_get_style_context (widget);
  gtk_style_context_save (context);
  gtk_style_context_add_class (context, "fade-overlay");

  GdkRGBA bg;
  gtk_style_context_get_background_color (context, GTK_STATE_FLAG_NORMAL, &bg);
  cairo_set_source_rgba (cr, bg.red, bg.green, bg.blue, overlay_opacity * bg.alpha);

  gint radius;
  gtk_style_context_get (context, GTK_STATE_FLAG_NORMAL,
			 GTK_STYLE_PROPERTY_BORDER_RADIUS, &radius,
			 NULL);

  GtkBorder margin;
  gtk_style_context_get_margin (context, GTK_STATE_FLAG_NORMAL, &margin);

  double x = margin.left,
         y = margin.top,
         width = allocation.width - margin.left - margin.right,
         height = allocation.height - margin.top - margin.bottom,
         degrees = G_PI / 180.0;

  cairo_new_sub_path (cr);
  cairo_arc (cr, x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees);
  cairo_arc (cr, x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees);
  cairo_arc (cr, x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees);
  cairo_arc (cr, x + radius, y + radius, radius, 180 * degrees, 270 * degrees);
  cairo_close_path (cr);
  cairo_fill (cr);

  gtk_style_context_restore (context);

  GTK_WIDGET_CLASS (eos_stack_parent_class)->draw (widget, cr);

  return TRUE;
}

static gboolean
eos_stack_transition_cb (GtkStack      *stack,
                         GdkFrameClock *frame_clock,
                         gpointer       user_data)
{
  EosStackPrivate *priv = eos_stack_get_instance_private (EOS_STACK (stack));
  gint64 now;
  gdouble t;

  now = gdk_frame_clock_get_frame_time (frame_clock);

  t = 1.0;
  if (now < priv->end_time)
    t = (now - priv->start_time) / (double) (priv->end_time - priv->start_time);

  if (!gtk_widget_get_mapped (GTK_WIDGET (stack)))
    {
      t = 1.0;
    }

  priv->transition_pos = t;

  return TRUE;
}

void
eos_stack_set_visible_child (EosStack  *stack,
                             GtkWidget *child,
                             gboolean show_overlay)
{
  EosStackPrivate *priv = eos_stack_get_instance_private (EOS_STACK (stack));
  GtkWidget *widget = GTK_WIDGET (stack);
  guint transition_duration;

  transition_duration = gtk_stack_get_transition_duration (stack);

  if (!priv->show_overlay && !show_overlay)
      priv->overlay_type = EOS_STACK_OVERLAY_TRANSITION_TYPE_NONE;
  else if (priv->show_overlay && show_overlay)
      priv->overlay_type = EOS_STACK_OVERLAY_TRANSITION_TYPE_VISIBLE;
  else if (!priv->show_overlay && show_overlay)
      priv->overlay_type = EOS_STACK_OVERLAY_TRANSITION_TYPE_SHOW;
  else
      priv->overlay_type = EOS_STACK_OVERLAY_TRANSITION_TYPE_HIDE;

  priv->show_overlay = show_overlay;
  priv->transition_pos = 0.0;
  priv->start_time = gdk_frame_clock_get_frame_time (gtk_widget_get_frame_clock (widget));
  priv->end_time = priv->start_time + (transition_duration * 1000);

  if (priv->tick_id == 0)
    priv->tick_id = gtk_widget_add_tick_callback (GTK_WIDGET (stack),
						  (GtkTickCallback) eos_stack_transition_cb,
						  stack, NULL);

  gtk_stack_set_visible_child (stack, child);
}

static void
eos_stack_class_init (EosStackClass *klass)
{
  GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);
  widget_class->draw = eos_stack_draw;
}

static void
eos_stack_init (EosStack *self)
{
  EosStackPrivate *priv = eos_stack_get_instance_private (self);
  priv->overlay_type = EOS_STACK_OVERLAY_TRANSITION_TYPE_NONE;
}

/* Public API */

/**
 * eos_stack_new:
 *
 * Creates a new default stack.
 *
 * Returns: the new stack
 */
GtkWidget *
eos_stack_new (void)
{
  return g_object_new (EOS_TYPE_STACK, NULL);
}
