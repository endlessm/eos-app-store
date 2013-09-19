#ifndef __EOS_APP_ENUMS_H__
#define __EOS_APP_ENUMS_H__

#include <glib-object.h>

G_BEGIN_DECLS

#define EOS_TYPE_APP_ICON_STATE         (eos_app_icon_state_get_type ())

typedef enum {
  EOS_APP_ICON_STATE_NORMAL,
  EOS_APP_ICON_STATE_ACTIVE,
  EOS_APP_ICON_STATE_HOVER
} EosAppIconState;

GType eos_app_icon_state_get_type (void);

#define EOS_TYPE_APP_STATE              (eos_app_state_get_type ())

typedef enum {
  EOS_APP_STATE_UNKNOWN,

  EOS_APP_STATE_INSTALLED,
  EOS_APP_STATE_UNINSTALLED,
  EOS_APP_STATE_UPDATABLE
} EosAppState;

GType eos_app_state_get_type (void);

#define EOS_TYPE_APP_CATEGORY           (eos_app_category_get_type ())

typedef enum {
  EOS_APP_CATEGORY_FEATURED,
  EOS_APP_CATEGORY_EDUCATION,
  EOS_APP_CATEGORY_LEISURE,
  EOS_APP_CATEGORY_UTILITIES,

  EOS_APP_CATEGORY_MY_APPLICATIONS
} EosAppCategory;

GType eos_app_category_get_type (void);

G_END_DECLS

#endif /* __EOS_APP_ENUMS_H__ */
