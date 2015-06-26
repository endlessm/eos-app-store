/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-cell.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

#include "eos-app-info-private.h"
#include "eos-flexy-grid.h"
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

  GtkWidget *stack;
  GtkWidget *revealer;
  GtkWidget *tile, *tile_selected;

  GtkWidget *title_label, *title_label_selected;
  GtkWidget *subtitle_label;
  GtkWidget *icon;

  EosAppInfo *info;

  cairo_surface_t *image;
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
  g_autoptr(GtkWidgetPath) widget_path = gtk_widget_path_new ();
  gtk_widget_path_append_type (widget_path, eos_app_cell_get_type ());

  GtkStyleContext *style_context = gtk_style_context_new ();
  gtk_style_context_set_path (style_context, widget_path);
  gtk_style_context_add_class (style_context, "app-cell-image");

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

static cairo_surface_t *
prepare_surface_from_file (EosAppCell *self,
                           const gchar *path,
                           gint image_width,
                           gint image_height,
                           GError **error)
{
  cairo_t *cr;

  g_autofree char *provider_data = g_strdup_printf (PROVIDER_DATA_FORMAT, path);
  g_autoptr(GtkCssProvider) provider = gtk_css_provider_new ();

  if (!gtk_css_provider_load_from_data (provider, provider_data, -1, error))
    return NULL;

  gtk_style_context_add_provider (self->image_context,
                                  GTK_STYLE_PROVIDER (provider),
                                  GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

  cairo_surface_t *surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                                         image_width, image_height);
  cairo_t *cr = cairo_create (surface);
  gtk_render_background (self->image_context, cr,
                         0, 0, image_width, image_height);
  cairo_destroy (cr);

  gtk_style_context_remove_provider (self->image_context, GTK_STYLE_PROVIDER (provider));

  return surface;
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
      g_value_set_object (value, self->info);
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
      gtk_label_set_text (GTK_LABEL (self->title_label_selected), g_value_get_string (value));
      break;

    case PROP_SUBTITLE:
      gtk_label_set_text (GTK_LABEL (self->subtitle_label), g_value_get_string (value));
      break;

    case PROP_APP_INFO:
      g_assert (self->info == NULL);
      self->info = g_value_dup_object (value);
      g_assert (self->info != NULL);
      break;

    case PROP_SELECTED:
      {
        self->is_selected = g_value_get_boolean (value);
        if (self->is_selected)
          {
            gtk_stack_set_visible_child (GTK_STACK (self->stack), self->tile_selected);
            gtk_revealer_set_reveal_child (GTK_REVEALER (self->revealer), TRUE);
          }
        else
          {
            gtk_stack_set_visible_child (GTK_STACK (self->stack), self->tile);
            gtk_revealer_set_reveal_child (GTK_REVEALER (self->revealer), FALSE);
          }
      }
      break;

    case PROP_ICON:
      {
        const char *icon_name = g_value_get_string (value);

        self->icon_name = g_strdup (icon_name);

        if (icon_name != NULL)
          gtk_image_set_from_icon_name (GTK_IMAGE (self->icon),
                                        icon_name,
                                        GTK_ICON_SIZE_DIALOG);
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
  g_clear_pointer (&self->image, (GDestroyNotify) cairo_surface_destroy);
  g_free (self->desktop_id);
  g_free (self->icon_name);
  g_clear_object (&self->info);

  G_OBJECT_CLASS (eos_app_cell_parent_class)->finalize (gobject);
}

static void
eos_app_cell_draw_normal (EosAppCell *self,
                          cairo_t *cr,
                          gint width,
                          gint height)
{
  gint image_width, image_height;
  GtkBorder image_margin;
  EosFlexyShape shape;

  if (self->image != NULL)
    goto out;

  shape = eos_flexy_grid_cell_get_shape (EOS_FLEXY_GRID_CELL (self));

  g_autofree char *path = NULL;
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

  g_autoptr(GError) error = NULL;
  image_width = width - self->cell_margin;
  image_height = height - self->cell_margin;
  self->image = prepare_surface_from_file (self, path, image_width, image_height, &error);

  if (error != NULL)
    g_warning ("Unable to load image at path '%s': %s", path, error->message);

out:
  if (self->image != NULL)
    {
      gtk_style_context_get_margin (self->image_context,
                                    GTK_STATE_FLAG_NORMAL,
                                    &image_margin);

      gtk_render_icon_surface (self->image_context,
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

  if (self->info == NULL)
    {
      g_critical ("No EosAppInfo found for cell %p", widget);
      return FALSE;
    }

  eos_app_cell_draw_normal (self, cr,
                            gtk_widget_get_allocated_width (widget),
                            gtk_widget_get_allocated_height (widget));

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
    g_param_spec_object ("app-info",
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
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS | G_PARAM_CONSTRUCT_ONLY);

  g_object_class_install_properties (oclass, NUM_PROPS, eos_app_cell_props);
}

static void
configure_style_for_subtitle_label (GtkLabel *label)
{
  gtk_style_context_add_class (gtk_widget_get_style_context (GTK_WIDGET (label)),
                               "app-cell-subtitle");

#if GTK_CHECK_VERSION (3, 16, 0)
  gtk_label_set_xalign (GTK_LABEL (label), 0);
  gtk_label_set_yalign (GTK_LABEL (label), 0);
#else
  gtk_misc_set_alignment (GTK_MISC (label), 0.0, 0.0);
#endif

  gtk_label_set_line_wrap (GTK_LABEL (label), TRUE);
  gtk_label_set_max_width_chars (GTK_LABEL (label), 50);
  gtk_label_set_ellipsize (GTK_LABEL (label), PANGO_ELLIPSIZE_END);
  gtk_label_set_lines (GTK_LABEL(label), 2);
}

static void
eos_app_cell_init (EosAppCell *self)
{
  GtkWidget *overlay = gtk_overlay_new ();
  gtk_widget_set_hexpand (GTK_WIDGET (overlay), TRUE);
  gtk_widget_set_vexpand (GTK_WIDGET (overlay), TRUE);
  gtk_container_add (GTK_CONTAINER (self), overlay);
  gtk_widget_show (overlay);

  GtkWidget *stack = gtk_stack_new ();
  self->stack = stack;
  gtk_stack_set_transition_type (GTK_STACK (self->stack), GTK_STACK_TRANSITION_TYPE_CROSSFADE);
  gtk_stack_set_transition_duration (GTK_STACK (self->stack), 350);
  gtk_container_add (GTK_CONTAINER (overlay), stack);

  /* Normal state */
  self->tile = gtk_frame_new (NULL);
  gtk_style_context_add_class (gtk_widget_get_style_context (self->tile),
                               "app-cell-frame");
  gtk_container_add (GTK_CONTAINER (self->stack), self->tile);
  gtk_widget_show (self->tile);

  GtkWidget *box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 2);
  gtk_widget_set_valign (box, GTK_ALIGN_END);
  gtk_widget_set_halign (box, GTK_ALIGN_START);
  gtk_container_add (GTK_CONTAINER (self->tile), box);
  gtk_widget_show (box);

  self->title_label = gtk_label_new ("");
  gtk_style_context_add_class (gtk_widget_get_style_context (self->title_label),
                               "app-cell-title");
  gtk_label_set_line_wrap (GTK_LABEL (self->title_label), TRUE);
  gtk_misc_set_alignment (GTK_MISC (self->title_label), 0.0, 0.5);
  gtk_container_add (GTK_CONTAINER (box), self->title_label);
  gtk_widget_show (self->title_label);

  /* We use a stack with a dummy label which will have two lines of
     text, so we can control the space allocated for the visible
     subtitle regardless of its text length, to match the UI spec. */
  GtkWidget *subtitle_stack = gtk_stack_new ();
  GtkWidget *two_line_label = gtk_label_new ("Lorem ipsum dolor sit amet,"
                                             "consectetur adipiscing elit");
  configure_style_for_subtitle_label (GTK_LABEL (two_line_label));
  gtk_stack_add_named (GTK_STACK (subtitle_stack), two_line_label, "invisible_label");

  self->subtitle_label = gtk_label_new ("");
  configure_style_for_subtitle_label (GTK_LABEL (self->subtitle_label));
  gtk_widget_show (self->subtitle_label);

  gtk_stack_add_named (GTK_STACK (subtitle_stack), self->subtitle_label, "visible_label");
  gtk_stack_set_visible_child_name (GTK_STACK (subtitle_stack), "visible_label");
  gtk_container_add (GTK_CONTAINER (box), subtitle_stack);
  gtk_widget_show (subtitle_stack);

  /* Selected state */
  self->tile_selected = gtk_frame_new (NULL);
  gtk_style_context_add_class (gtk_widget_get_style_context (self->tile_selected),
                               "app-cell-frame");
  gtk_style_context_add_class (gtk_widget_get_style_context (self->tile_selected),
                               "select");
  gtk_container_add (GTK_CONTAINER (stack), self->tile_selected);
  gtk_widget_show (self->tile_selected);

  GtkWidget *frame = gtk_frame_new (NULL);
  gtk_style_context_add_class (gtk_widget_get_style_context (frame),
                               "app-cell-frame");
  gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_NONE);
  gtk_widget_set_hexpand (frame, TRUE);
  gtk_widget_set_vexpand (frame, TRUE);
  gtk_overlay_add_overlay (GTK_OVERLAY (overlay), frame);
  gtk_widget_show (frame);

  GtkWidget *revealer = gtk_revealer_new ();
  self->revealer = revealer;
  gtk_widget_set_valign (self->revealer, GTK_ALIGN_END);
  gtk_revealer_set_transition_duration (GTK_REVEALER (self->revealer), 350);
  gtk_revealer_set_transition_type (GTK_REVEALER (self->revealer),
                                    GTK_REVEALER_TRANSITION_TYPE_SLIDE_UP);
  gtk_container_add (GTK_CONTAINER (frame), self->revealer);
  gtk_widget_show (self->revealer);

  GtkWidget *box_selected = gtk_box_new (GTK_ORIENTATION_VERTICAL, 2);
  gtk_container_add (GTK_CONTAINER (self->revealer), box_selected);
  gtk_widget_show (box_selected);
  gtk_style_context_add_class (gtk_widget_get_style_context (box_selected),
                               "select");

  GtkWidget *hbox = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 13);
  gtk_widget_set_hexpand (hbox, TRUE);
  gtk_container_add (GTK_CONTAINER (box_selected), hbox);
  gtk_widget_show (hbox);

  self->icon = gtk_image_new ();
  gtk_widget_show (self->icon);
  gtk_style_context_add_class (gtk_widget_get_style_context (self->icon),
                               "app-cell-icon");
  gtk_widget_set_halign (self->icon, GTK_ALIGN_START);
  gtk_container_add (GTK_CONTAINER (hbox), self->icon);

  GtkWidget *arrow_selected = gtk_image_new_from_resource ("/com/endlessm/appstore/icon_arrow_thumb.png");
  gtk_widget_show (arrow_selected);
  gtk_widget_set_valign (arrow_selected, GTK_ALIGN_CENTER);
  gtk_container_add (GTK_CONTAINER (hbox), arrow_selected);

  self->title_label_selected = gtk_label_new ("");
  gtk_style_context_add_class (gtk_widget_get_style_context (self->title_label_selected),
                               "app-cell-title");
  gtk_label_set_line_wrap (GTK_LABEL (self->title_label_selected), TRUE);
  gtk_misc_set_alignment (GTK_MISC (self->title_label_selected), 0.0, 0.5);
  gtk_container_add (GTK_CONTAINER (box_selected), self->title_label_selected);
  gtk_widget_show (self->title_label_selected);

  self->image_context = eos_app_info_get_cell_style_context ();
  self->cell_margin = eos_app_info_get_cell_margin_for_context (self->image_context);
}

gint
eos_app_info_get_cell_margin (void)
{
  g_autoptr(GtkStyleContext) context = eos_app_info_get_cell_style_context ();

  return eos_app_info_get_cell_margin_for_context (context);
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
 * eos_app_info_create_cell:
 * @info:
 * @icon_name: (allow-none):
 *
 * ...
 *
 * Returns: (transfer full) (type EosAppCell): ...
 */
GtkWidget *
eos_app_info_create_cell (const EosAppInfo *info,
                          const gchar *icon_name)
{
  if (info == NULL)
    return NULL;

  GtkWidget *res = g_object_new (eos_app_cell_get_type (),
                                 "shape", eos_app_info_get_shape_for_cell (info),
                                 "title", eos_app_info_get_title (info),
                                 "subtitle", eos_app_info_get_subtitle (info),
                                 "desktop-id", info->desktop_id,
                                 "app-info", info,
                                 "icon", icon_name,
                                 NULL);

  g_object_ref_sink (res);

  return res;
}
