#ifndef __EOS_APP_INFO_PRIVATE_H__
#define __EOS_APP_INFO_PRIVATE_H__

#include "eos-app-info.h"

G_BEGIN_DECLS

/*
 * EosAppInfo
 */
struct _EosAppInfo
{
  volatile int ref_count;

  char *application_id;
  char *desktop_id;
  char *content_id;

  char *title;
  char *subtitle;
  char *description;
  char *server_locale;
  char *installed_locale;

  char *installed_version;
  char *available_version;

  char *info_filename;

  char *bundle_uri;
  char *signature_uri;
  char *bundle_hash;

  char *delta_bundle_uri;
  char *delta_signature_uri;
  char *delta_bundle_hash;

  gint64 installed_size;
  gint64 server_installed_size;

  char *square_img;
  char *featured_img;
  char *icon_name;

  char **screenshots;
  guint n_screenshots;

  EosFlexyShape shape;

  EosAppCategory category;

  gint64 installation_time;

  guint is_featured : 1;
  guint is_offline : 1;
  guint installed_on_secondary_storage : 1;
  guint server_on_secondary_storage : 1;
  guint is_available : 1;
  guint is_installed : 1;
  guint has_launcher : 1;
  guint has_override : 1;
};

G_END_DECLS

#endif
