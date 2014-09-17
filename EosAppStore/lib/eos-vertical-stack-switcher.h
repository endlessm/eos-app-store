/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef __EOS_VERTICAL_STACK_SWITCHER_H__
#define __EOS_VERTICAL_STACK_SWITCHER_H__

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define EOS_TYPE_VERTICAL_STACK_SWITCHER            (eos_vertical_stack_switcher_get_type ())
#define EOS_VERTICAL_STACK_SWITCHER(obj)            (G_TYPE_CHECK_INSTANCE_CAST ((obj), EOS_TYPE_VERTICAL_STACK_SWITCHER, EosVerticalStackSwitcher))
#define EOS_VERTICAL_STACK_SWITCHER_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST ((klass), EOS_TYPE_VERTICAL_STACK_SWITCHER, EosVerticalStackSwitcherClass))
#define EOS_IS_VERTICAL_STACK_SWITCHER(obj)         (G_TYPE_CHECK_INSTANCE_TYPE ((obj), EOS_TYPE_VERTICAL_STACK_SWITCHER))
#define EOS_IS_VERTICAL_STACK_SWITCHER_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), EOS_TYPE_VERTICAL_STACK_SWITCHER))
#define EOS_VERTICAL_STACK_SWITCHER_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS ((obj), EOS_TYPE_VERTICAL_STACK_SWITCHER, EosVerticalStackSwitcherClass))

typedef struct _EosVerticalStackSwitcher              EosVerticalStackSwitcher;
typedef struct _EosVerticalStackSwitcherClass         EosVerticalStackSwitcherClass;

struct _EosVerticalStackSwitcher
{
  GtkStackSwitcher widget;
};

struct _EosVerticalStackSwitcherClass
{
  GtkStackSwitcherClass parent_class;
};

GType        eos_vertical_stack_switcher_get_type          (void) G_GNUC_CONST;
GtkWidget *  eos_vertical_stack_switcher_new               (void);

G_END_DECLS

#endif /* __GTK_STACK_SWITCHER_H__ */
