/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#ifndef __EOS_APP_ENUMS_H__
#define __EOS_APP_ENUMS_H__

#include <glib-object.h>

G_BEGIN_DECLS

#define EOS_TYPE_APP_STATE              (eos_app_state_get_type ())

typedef enum {
  EOS_APP_STATE_UNKNOWN,
  EOS_APP_STATE_INSTALLED,
  EOS_APP_STATE_AVAILABLE,
  EOS_APP_STATE_UPDATABLE
} EosAppState;

GType eos_app_state_get_type (void);

#define EOS_TYPE_APP_CATEGORY           (eos_app_category_get_type ())

typedef enum {
  EOS_APP_CATEGORY_EDUCATION,
  EOS_APP_CATEGORY_GAMES,
  EOS_APP_CATEGORY_RESOURCES,
  EOS_APP_CATEGORY_UTILITIES,
  EOS_APP_CATEGORY_INSTALLED,
  EOS_APP_CATEGORY_ALL
} EosAppCategory;

GType eos_app_category_get_type (void);

#define EOS_TYPE_APP_CATEGORY           (eos_app_category_get_type ())

typedef enum {
  EOS_LINK_CATEGORY_NEWS,
  EOS_LINK_CATEGORY_SPORTS,
  EOS_LINK_CATEGORY_EDUCATION,
  EOS_LINK_CATEGORY_ENTERTAINMENT,
  EOS_LINK_CATEGORY_LOCAL
} EosLinkCategory;

GType eos_link_category_get_type (void);

#define EOS_TYPE_FLEXY_SHAPE            (eos_flexy_shape_get_type ())

/**
 * EosFlexyShape:
 * @EOS_FLEXY_SHAPE_SMALL: 1x1 shape for small cells
 * @EOS_FLEXY_SHAPE_MEDIUM_HORIZONTAL: 2x1 <quote>landscape</quote> shape for
 * medium cells
 * @EOS_FLEXY_SHAPE_MEDIUM_VERTICAL: 1x2 <quote>portrait</quote> shape for
 * medium cells
 * @EOS_FLEXY_SHAPE_LARGE: 2x2 shape for large cells
 *
 * Sizes for flexible-layout cells in `EosFlexyGrid`.
 */
typedef enum
{
  EOS_FLEXY_SHAPE_SMALL,
  EOS_FLEXY_SHAPE_MEDIUM_HORIZONTAL,
  EOS_FLEXY_SHAPE_MEDIUM_VERTICAL,
  EOS_FLEXY_SHAPE_LARGE
} EosFlexyShape;

GType eos_flexy_shape_get_type (void) G_GNUC_CONST;

#define EOS_TYPE_STORAGE_TYPE (eos_storage_type_get_type ())

typedef enum
{
  EOS_STORAGE_TYPE_UNKNOWN,
  EOS_STORAGE_TYPE_PRIMARY,
  EOS_STORAGE_TYPE_SECONDARY
} EosStorageType;

GType eos_storage_type_get_type (void);

#define EOS_APP_STORE_ERROR        (eos_app_store_error_quark ())

GQuark eos_app_store_error_quark (void);

typedef enum {
  EOS_APP_STORE_ERROR_FAILED,
  EOS_APP_STORE_ERROR_INSTALLED,
  EOS_APP_STORE_ERROR_NOT_INSTALLED,
  EOS_APP_STORE_ERROR_NO_UPDATE_AVAILABLE,
  EOS_APP_STORE_ERROR_DISK_FULL,
  EOS_APP_STORE_ERROR_INSTALL_FAILED,
  EOS_APP_STORE_ERROR_UNINSTALL_FAILED,
  EOS_APP_STORE_ERROR_CHECKSUM_MISSING,
  EOS_APP_STORE_ERROR_SIGNATURE_MISSING,
  EOS_APP_STORE_ERROR_APP_REFRESH_PARTIAL_FAILURE,
  EOS_APP_STORE_ERROR_APP_REFRESH_FAILURE,
} EosAppStoreError;

G_END_DECLS

#endif /* __EOS_APP_ENUMS_H__ */
