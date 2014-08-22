/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-enums.h"
#include <glib.h>

#ifndef EOS_DEFINE_ENUM_TYPE

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

#endif

EOS_DEFINE_ENUM_TYPE (EosAppState, eos_app_state,
                      EOS_ENUM_VALUE (EOS_APP_STATE_UNKNOWN, unknown)
                      EOS_ENUM_VALUE (EOS_APP_STATE_INSTALLED, installed)
                      EOS_ENUM_VALUE (EOS_APP_STATE_UNINSTALLED, uninstalled)
                      EOS_ENUM_VALUE (EOS_APP_STATE_UPDATABLE, updatable))

EOS_DEFINE_ENUM_TYPE (EosAppCategory, eos_app_category,
                      EOS_ENUM_VALUE (EOS_APP_CATEGORY_RESOURCES, resources)
                      EOS_ENUM_VALUE (EOS_APP_CATEGORY_EDUCATION, education)
                      EOS_ENUM_VALUE (EOS_APP_CATEGORY_GAMES, games)
                      EOS_ENUM_VALUE (EOS_APP_CATEGORY_UTILITIES, utilities)
                      EOS_ENUM_VALUE (EOS_APP_CATEGORY_INSTALLED, installed))

EOS_DEFINE_ENUM_TYPE (EosLinkCategory, eos_link_category,
                      EOS_ENUM_VALUE (EOS_LINK_CATEGORY_NEWS, news)
                      EOS_ENUM_VALUE (EOS_LINK_CATEGORY_SPORTS, sports)
                      EOS_ENUM_VALUE (EOS_LINK_CATEGORY_EDUCATION, education)
                      EOS_ENUM_VALUE (EOS_LINK_CATEGORY_ENTERTAINMENT, entertainment)
                      EOS_ENUM_VALUE (EOS_LINK_CATEGORY_LOCAL, local))
