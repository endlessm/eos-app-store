/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-vertical-stack-switcher.h"

typedef struct _EosVerticalStackSwitcherPrivate EosVerticalStackSwitcherPrivate;
struct _EosVerticalStackSwitcherPrivate {
  GHashTable *buttons;
};

G_DEFINE_TYPE_WITH_PRIVATE (EosVerticalStackSwitcher, eos_vertical_stack_switcher, GTK_TYPE_STACK_SWITCHER)

static void
eos_vertical_stack_switcher_finalize (GObject *object)
{
  EosVerticalStackSwitcher *self;
  EosVerticalStackSwitcherPrivate *priv;

  self = EOS_VERTICAL_STACK_SWITCHER (object);
  priv = eos_vertical_stack_switcher_get_instance_private (self);

  g_clear_pointer (&priv->buttons, g_hash_table_unref);

  G_OBJECT_CLASS (eos_vertical_stack_switcher_parent_class)->finalize (object);
}

static void
set_align_for_child (GtkWidget *widget)
{
  GtkWidget *child;

  child = gtk_bin_get_child (GTK_BIN (widget));
  if (child != NULL)
    gtk_widget_set_halign (child, GTK_ALIGN_START);
}

static void
eos_vertical_stack_switcher_remove (GtkContainer *container,
				    GtkWidget *widget)
{
  EosVerticalStackSwitcher *self;
  EosVerticalStackSwitcherPrivate *priv;

  self = EOS_VERTICAL_STACK_SWITCHER (container);
  priv = eos_vertical_stack_switcher_get_instance_private (self);

  g_signal_handlers_disconnect_by_func (widget, set_align_for_child, container);
  g_hash_table_remove (priv->buttons, widget);

  GTK_CONTAINER_CLASS (eos_vertical_stack_switcher_parent_class)->remove (container, widget);
}

static void
eos_vertical_stack_switcher_add (GtkContainer *container,
				 GtkWidget *widget)
{
  EosVerticalStackSwitcher *self;
  EosVerticalStackSwitcherPrivate *priv;

  self = EOS_VERTICAL_STACK_SWITCHER (container);
  priv = eos_vertical_stack_switcher_get_instance_private (self);

  GTK_CONTAINER_CLASS (eos_vertical_stack_switcher_parent_class)->add (container, widget);

  if (!GTK_IS_BUTTON (widget))
    return;

  g_signal_connect (widget, "add", G_CALLBACK (set_align_for_child), container);
  g_hash_table_add (priv->buttons, widget);

  set_align_for_child (widget);
}

static void
eos_vertical_stack_switcher_init (EosVerticalStackSwitcher *switcher)
{
  EosVerticalStackSwitcherPrivate *priv;

  priv = eos_vertical_stack_switcher_get_instance_private (switcher);
  priv->buttons = g_hash_table_new (NULL, NULL);

  gtk_orientable_set_orientation (GTK_ORIENTABLE (switcher), GTK_ORIENTATION_VERTICAL);
}

static void
eos_vertical_stack_switcher_class_init (EosVerticalStackSwitcherClass *class)
{
  GObjectClass *oclass = G_OBJECT_CLASS (class);
  GtkContainerClass *cclass = GTK_CONTAINER_CLASS (class);

  cclass->add = eos_vertical_stack_switcher_add;
  cclass->remove = eos_vertical_stack_switcher_remove;

  oclass->finalize = eos_vertical_stack_switcher_finalize;
}

/**
 * eos_vertical_stack_switcher_new:
 *
 * Create a new #EosVerticalStackSwitcher.
 *
 * Returns: a new #EosVerticalStackSwitcher.
 */
GtkWidget *
eos_vertical_stack_switcher_new (void)
{
  return g_object_new (EOS_TYPE_VERTICAL_STACK_SWITCHER, NULL);
}
