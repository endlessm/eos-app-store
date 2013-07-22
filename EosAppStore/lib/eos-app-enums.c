#include "config.h"

#include "eos-app-enums.h"
#include <glib.h>

#define EOS_ENUM_VALUE(value, nick)     { value, #value, #nick },

#define EOS_DEFINE_ENUM_TYPE(EnumType, enum_type, values) \
GType \
enum_type##_get_type (void) \
{ \
  static volatile gsize g_define_type_id__volatile = 0; \
  if (g_once_init_enter (&g_define_type_id__volatile)) \
    { \
      static const GEnumValue v[] = { \
        values \
	{ 0, NULL, NULL }, \
      }; \
      GType g_define_type_id = \
        g_enum_register_static (g_intern_static_string (#EnumType), v); \
\
      g_once_init_leave (&g_define_type_id__volatile, g_define_type_id); \
    } \
  return g_define_type_id__volatile; \
}

EOS_DEFINE_ENUM_TYPE (EosAppIconState, eos_app_icon_state,
                      EOS_ENUM_VALUE (EOS_APP_ICON_STATE_NORMAL, normal)
                      EOS_ENUM_VALUE (EOS_APP_ICON_STATE_ACTIVE, active)
                      EOS_ENUM_VALUE (EOS_APP_ICON_STATE_HOVER, hover))
