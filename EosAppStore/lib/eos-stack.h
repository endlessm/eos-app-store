/* Copyright 2014 Endless Mobile, Inc. */

#ifndef EOS_STACK_H
#define EOS_STACK_H

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define EOS_TYPE_STACK eos_stack_get_type()

#define EOS_STACK(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), \
  EOS_TYPE_STACK, EosStack))

#define EOS_STACK_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), \
  EOS_TYPE_STACK, EosStackClass))

#define EOS_IS_STACK(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), \
  EOS_TYPE_STACK))

#define EOS_IS_STACK_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), \
  EOS_TYPE_STACK))

#define EOS_STACK_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), \
  EOS_TYPE_STACK, EosStackClass))

typedef struct _EosStack EosStack;
typedef struct _EosStackClass EosStackClass;

/**
 * EosStack:
 *
 * This structure contains no public members.
 */
struct _EosStack
{
  GtkStack parent;
};

struct _EosStackClass
{
  GtkStackClass parent_class;
};

GType        eos_stack_get_type                            (void) G_GNUC_CONST;

void         eos_stack_set_transition_duration             (EosStack *stack,
                                                            guint duration);

void         eos_stack_set_visible_child                   (GtkStack  *stack,
                                                            GtkWidget *child,
                                                            gboolean show_overlay);

GtkWidget   *eos_stack_new                                 (void);

G_END_DECLS

#endif /* EOS_STACK_H */
