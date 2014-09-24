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
tweak_button_child (EosVerticalStackSwitcher *self,
                    GtkWidget *button)
{
  GtkWidget *child;
  GtkWidget *stack;
  GtkWidget *box;
  GtkWidget *stack_child;
  GtkWidget *widget;
  gchar *icon_name, *title;
  GIcon *icon;
  GFile *gfile;

  stack_child = g_object_get_data (G_OBJECT (button), "stack-child");
  if (stack_child == NULL)
    return;

  child = gtk_bin_get_child (GTK_BIN (button));
  if (child != NULL)
    {
      if (GTK_IS_BOX (child))
        return;

      gtk_widget_destroy (child);
    }

  title = icon_name = NULL;
  box = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 6);
  stack = GTK_WIDGET (gtk_stack_switcher_get_stack (GTK_STACK_SWITCHER (self)));

  gtk_container_child_get (GTK_CONTAINER (stack), stack_child,
                           "title", &title,
                           "icon-name", &icon_name,
                           NULL);

  if (icon_name != NULL)
    {
      gfile = g_file_new_for_uri (icon_name);
      icon = g_file_icon_new (gfile);
      g_object_unref (gfile);

      widget = gtk_image_new_from_gicon (icon, GTK_ICON_SIZE_MENU);
      gtk_container_add (GTK_CONTAINER (box), widget);
      g_object_unref (icon);
    }

  if (title != NULL)
    {
      widget = gtk_label_new (title);
      gtk_widget_set_halign (widget, GTK_ALIGN_START);
      gtk_container_add (GTK_CONTAINER (box), widget);
    }

  gtk_widget_set_halign (box, GTK_ALIGN_START);
  gtk_widget_show_all (box);
  gtk_container_add (GTK_CONTAINER (button), box);

  g_free (title);
  g_free (icon_name);
}

static void
button_child_added (GtkContainer *button,
                    GtkWidget *child,
                    EosVerticalStackSwitcher *self)
{
  tweak_button_child (self, GTK_WIDGET (button));
}

static GType
eos_vertical_stack_switcher_child_type (GtkContainer *container)
{
  return GTK_TYPE_BUTTON;
}

static void
eos_vertical_stack_switcher_remove (GtkContainer *container,
				    GtkWidget *widget)
{
  EosVerticalStackSwitcher *self;
  EosVerticalStackSwitcherPrivate *priv;

  self = EOS_VERTICAL_STACK_SWITCHER (container);
  priv = eos_vertical_stack_switcher_get_instance_private (self);

  g_signal_handlers_disconnect_by_func (widget, tweak_button_child, container);
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

  g_assert (GTK_IS_BUTTON (widget));

  g_signal_connect (widget, "add", G_CALLBACK (button_child_added), self);
  g_hash_table_add (priv->buttons, widget);

  tweak_button_child (self, widget);
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
  cclass->child_type = eos_vertical_stack_switcher_child_type;

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
