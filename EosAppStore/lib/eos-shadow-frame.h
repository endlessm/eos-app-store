#ifndef EOS_SHADOW_FRAME_H
#define EOS_SHADOW_FRAME_H

#include <glib-object.h>
#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include "eos-app-enums.h"

G_BEGIN_DECLS

#define EOS_TYPE_SHADOW_FRAME        eos_shadow_frame_get_type ()

#define EOS_SHADOW_FRAME(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), EOS_TYPE_SHADOW_FRAME, EosShadowFrame))

#define EOS_SHADOW_FRAME_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), EOS_TYPE_SHADOW_FRAME, EosShadowFrameClass))

#define EOS_IS_SHADOW_FRAME(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), EOS_TYPE_SHADOW_FRAME))

#define EOS_IS_SHADOW_FRAME_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), EOS_TYPE_SHADOW_FRAME))

#define EOS_SHADOW_FRAME_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), EOS_TYPE_SHADOW_FRAME, EosShadowFrameClass))


typedef struct _EosShadowFrame      EosShadowFrame;
typedef struct _EosShadowFrameClass EosShadowFrameClass;
typedef struct _EosShadowFramePrivate EosShadowFramePrivate;

struct _EosShadowFrame
{
  GtkBin parent;

  EosShadowFramePrivate *priv;
};

struct _EosShadowFrameClass
{
  GtkBinClass parent_class;
};

GType eos_shadow_frame_get_type (void);

GtkWidget *    eos_shadow_frame_new                (void);

G_END_DECLS

#endif /* EOS_SHADOW_FRAME_H */
