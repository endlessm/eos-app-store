#ifndef __EOS_APP_ENUMS_H__
#define __EOS_APP_ENUMS_H__

#include <glib-object.h>

G_BEGIN_DECLS

typedef enum {
  EOS_APP_ICON_STATE_NORMAL,
  EOS_APP_ICON_STATE_ACTIVE,
  EOS_APP_ICON_STATE_HOVER
} EosAppIconState;

GType eos_app_icon_state_get_type (void);

G_END_DECLS

#endif /* __EOS_APP_ENUMS_H__ */
