/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-info-private.h"
#include "eos-app-enums.h"
#include "eos-app-log.h"
#include "eos-app-utils.h"
#include "eos-flexy-grid.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include <locale.h>
#include <glib/gi18n.h>

G_DEFINE_TYPE (EosAppInfo, eos_app_info, G_TYPE_OBJECT)

enum {
  PROP_0,
  PROP_APPLICATION_ID,
  PROP_INSTALLED_SIZE,
  PROP_STATE,
  NUM_PROPS,
};

static GParamSpec *properties[NUM_PROPS] = { NULL, };

enum {
  DOWNLOAD_PROGRESS,

  LAST_SIGNAL
};

static guint eos_app_info_signals[LAST_SIGNAL] = { 0, };

/* installed keyfile keys */
static const gchar *FILE_KEYS[] = {
  "app_id",
  "app_name",
  "version",
  "locale",
  "installed_size",
  "secondary_storage",
  NULL,
  NULL,
  NULL,
};

/* JSON fields from app server */
static const gchar *JSON_KEYS[] = {
  "appId",
  "appName",
  "codeVersion",
  "Locale",
  "installedSize",
  "secondaryStorage",
  "downloadLink",
  "signatureLink",
  "shaHash",
  "isDiff",
};

/* Keep the key ids in sync with the names above */
enum {
  APP_ID,
  APP_NAME,
  CODE_VERSION,
  LOCALE,
  INSTALLED_SIZE,
  SECONDARY_STORAGE,
  DOWNLOAD_LINK,
  SIGNATURE_LINK,
  SHA_HASH,
  IS_DIFF,

  N_KEYS
};

static gboolean
language_is_valid (const char *id)
{
  int len = strlen (id);

  /* This is a bit hacky for now. We limit locales to
   * be of the xx or xx_YY forms.
   */
  if (len != 5 && len != 2)
    return FALSE;

  if (!g_ascii_islower (id[0]) || !g_ascii_islower (id[1]))
    return FALSE;

  if (len == 5 &&
      (id[2] != '_' || !g_ascii_isupper (id[3]) || !g_ascii_isupper (id[4])))
    return FALSE;

  return TRUE;
}

static char *
content_id_from_application_id (const char *application_id)
{
  /* This function translates an application ID to the ID used in the content
   * JSON. These two will typically be the same, except for endless knowledge apps.
   */
  if (!g_str_has_prefix (application_id, "com.endlessm."))
    return g_strdup (application_id);

  /* Find the last dash in the application ID */
  char *ptr = g_strrstr (application_id, "-");
  if (ptr == NULL)
    return g_strdup (application_id);

  /* Verify that this is a valid locale */
  if (language_is_valid (ptr + 1))
    return g_strndup (application_id, ptr - application_id);

  return g_strdup (application_id);
}

static void
eos_app_info_set_application_id (EosAppInfo *info,
                                 const char *application_id)
{
  info->application_id = g_strdup (application_id);
  info->content_id = content_id_from_application_id (application_id);
  info->desktop_id = g_strdup_printf ("%s.desktop", application_id);
}

static void
eos_app_info_get_property (GObject    *gobject,
                           guint       prop_id,
                           GValue     *value,
                           GParamSpec *pspec)
{
  EosAppInfo *info = (EosAppInfo *) gobject;

  switch (prop_id)
    {
    case PROP_APPLICATION_ID:
      g_value_set_string (value, eos_app_info_get_application_id (info));
      break;
    case PROP_INSTALLED_SIZE:
      g_value_set_int64 (value, eos_app_info_get_installed_size (info));
      break;
    case PROP_STATE:
      g_value_set_enum (value, eos_app_info_get_state (info));
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

static void
eos_app_info_set_property (GObject      *gobject,
                           guint         prop_id,
                           const GValue *value,
                           GParamSpec   *pspec)
{
  EosAppInfo *info = (EosAppInfo *) gobject;

  switch (prop_id)
    {
    case PROP_APPLICATION_ID:
      eos_app_info_set_application_id (info, g_value_get_string (value));
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
    }
}

void
eos_app_info_clear_server_update_attributes (EosAppInfo *info)
{
  g_clear_pointer (&info->available_version, g_free);

  g_clear_pointer (&info->bundle_uri, g_free);
  g_clear_pointer (&info->signature_uri, g_free);
  g_clear_pointer (&info->bundle_hash, g_free);

  g_clear_pointer (&info->delta_bundle_uri, g_free);
  g_clear_pointer (&info->delta_signature_uri, g_free);
  g_clear_pointer (&info->delta_bundle_hash, g_free);

  g_clear_pointer (&info->server_locale, g_free);

  /* Meta fields that need clearing */
  info->is_available = FALSE;
}

static void
eos_app_info_clear_installed_attributes (EosAppInfo *info)
{
  g_clear_pointer (&info->installed_version, g_free);
  g_clear_pointer (&info->installed_locale, g_free);

  info->computed_installed_size = 0;
  info->installed_size_computed = FALSE;
  info->info_installed_size = 0;
  info->installation_time = -1;
  info->storage_type = EOS_STORAGE_TYPE_PRIMARY;
}

static void
eos_app_info_finalize (GObject *gobject)
{
  EosAppInfo *info = (EosAppInfo *) gobject;

  g_free (info->application_id);
  g_free (info->desktop_id);
  g_free (info->content_id);
  g_free (info->title);
  g_free (info->subtitle);
  g_free (info->description);
  g_free (info->square_img);
  g_free (info->featured_img);

  g_cancellable_cancel (info->size_computation_cancellable);
  g_clear_object (&info->size_computation_cancellable);

  eos_app_info_clear_installed_attributes (info);
  eos_app_info_clear_server_update_attributes (info);

  g_free (info->icon_name);
  g_free (info->info_filename);
  g_clear_object (&info->application_dir);
  g_strfreev (info->screenshots);

  G_OBJECT_CLASS (eos_app_info_parent_class)->finalize (gobject);
}

static void
eos_app_info_init (EosAppInfo *info)
{
  info->storage_type = EOS_STORAGE_TYPE_PRIMARY;
  info->shape = EOS_FLEXY_SHAPE_SMALL;
  info->installation_time = -1;
}

static void
eos_app_info_class_init (EosAppInfoClass *klass)
{
  GObjectClass *oclass = G_OBJECT_CLASS (klass);

  oclass->get_property = eos_app_info_get_property;
  oclass->set_property = eos_app_info_set_property;
  oclass->finalize = eos_app_info_finalize;

  properties[PROP_APPLICATION_ID] =
    g_param_spec_string ("application-id",
                         "Application ID",
                         "The application ID",
                         "",
                         G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS | G_PARAM_CONSTRUCT_ONLY);
  properties[PROP_INSTALLED_SIZE] =
    g_param_spec_int64 ("installed-size",
                        "Installed size",
                        "The application installed size",
                        -1, G_MAXINT64, 0,
                        G_PARAM_READABLE | G_PARAM_STATIC_STRINGS);
  properties[PROP_STATE] =
    g_param_spec_enum ("state",
                       "Application state",
                       "The application state",
                       EOS_TYPE_APP_STATE,
                       EOS_APP_STATE_UNKNOWN,
                       G_PARAM_READABLE | G_PARAM_STATIC_STRINGS);

  eos_app_info_signals[DOWNLOAD_PROGRESS] =
    g_signal_new (g_intern_static_string ("download-progress"),
                  G_OBJECT_CLASS_TYPE (klass),
                  G_SIGNAL_RUN_LAST,
                  0,
                  NULL, NULL,
                  NULL,
                  G_TYPE_NONE, 2,
                  G_TYPE_INT64,   /* current progress */
                  G_TYPE_INT64);  /* total size */

  g_object_class_install_properties (oclass, NUM_PROPS, properties);
}

EosAppInfo *
eos_app_info_new (const char *application_id)
{
  return g_object_new (EOS_TYPE_APP_INFO,
                       "application-id", application_id,
                       NULL);
}

const char *
eos_app_info_get_title (const EosAppInfo *info)
{
  return g_dpgettext2 (CONTENT_GETTEXT_PACKAGE, "title", info->title);
}

const char *
eos_app_info_get_subtitle (const EosAppInfo *info)
{
  return g_dpgettext2 (CONTENT_GETTEXT_PACKAGE, "subtitle", info->subtitle);
}

/**
 * eos_app_info_get_desktop_id:
 * @info: an #EosAppInfo
 *
 * Returns the desktop ID of @info. This is the application ID
 * with a .desktop suffix.
 *
 * Returns: the desktop ID.
 */
const char *
eos_app_info_get_desktop_id (const EosAppInfo *info)
{
  return info->desktop_id;
}

/**
 * eos_app_info_get_application_id:
 * @info: an #EosAppInfo
 *
 * Returns the application ID of @info. This is the desktop ID
 * without the .desktop suffix.
 *
 * Returns: the application ID.
 */
const char *
eos_app_info_get_application_id (const EosAppInfo *info)
{
  return info->application_id;
}

const char *
eos_app_info_get_content_id (const EosAppInfo *info)
{
  return info->content_id;
}

const char *
eos_app_info_get_description (const EosAppInfo *info)
{
  return g_dpgettext2 (CONTENT_GETTEXT_PACKAGE, "description", info->description);
}

const char *
eos_app_info_get_installed_version (const EosAppInfo *info)
{
  return info->installed_version;
}

const char *
eos_app_info_get_available_version (const EosAppInfo *info)
{
  return info->available_version;
}

const char *
eos_app_info_get_locale (const EosAppInfo *info)
{
  if (info->installed_locale)
    return info->installed_locale;

  return info->server_locale;
}

const char *
eos_app_info_get_bundle_uri (const EosAppInfo *info)
{
  return info->bundle_uri;
}

const char *
eos_app_info_get_signature_uri (const EosAppInfo *info)
{
  return info->signature_uri;
}

const char *
eos_app_info_get_bundle_hash (const EosAppInfo *info)
{
  return info->bundle_hash;
}

const char *
eos_app_info_get_delta_bundle_uri (const EosAppInfo *info)
{
  return info->delta_bundle_uri;
}

const char *
eos_app_info_get_delta_signature_uri (const EosAppInfo *info)
{
  return info->delta_signature_uri;
}

const char *
eos_app_info_get_delta_bundle_hash (const EosAppInfo *info)
{
  return info->delta_bundle_hash;
}

gboolean
eos_app_info_get_has_delta_update (const EosAppInfo *info)
{
  return info->delta_bundle_uri && info->delta_signature_uri &&
    info->delta_bundle_hash;
}

gboolean
eos_app_info_is_featured (const EosAppInfo *info)
{
  return info->is_featured;
}

gboolean
eos_app_info_is_offline (const EosAppInfo *info)
{
  return info->is_offline;
}

static void
compute_installed_size_usage_ready (GObject *source,
                                    GAsyncResult *res,
                                    gpointer user_data)
{
  GError *error = NULL;
  GFile *target_dir = G_FILE (source);
  EosAppInfo *info = user_data;

  guint64 disk_usage;
  g_file_measure_disk_usage_finish (target_dir, res,
                                    &disk_usage, NULL, NULL,
                                    &error);

  g_clear_object (&info->size_computation_cancellable);

  if (error != NULL)
    {
      eos_app_log_error_message ("Could not retrieve disk usage for %s: %s",
                                 eos_app_info_get_desktop_id (info),
                                 error->message);
      g_error_free (error);
    }
  else
    {
      info->computed_installed_size = (gint64) disk_usage;
      g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_INSTALLED_SIZE]);
    }

  g_object_unref (info);
}

static void
compute_installed_size (EosAppInfo *info)
{
  if (!eos_app_info_is_store_installed (info))
    return;

  if (info->installed_size_computed)
    return;

  if (info->size_computation_cancellable != NULL)
    return;

  info->installed_size_computed = TRUE;
  info->size_computation_cancellable = g_cancellable_new ();

  g_file_measure_disk_usage_async (info->application_dir,
                                   G_FILE_MEASURE_NONE,
                                   G_PRIORITY_DEFAULT,
                                   info->size_computation_cancellable,
                                   NULL, NULL,
                                   compute_installed_size_usage_ready,
                                   g_object_ref (info));
}

static gint64
eos_app_info_get_server_installed_size (const EosAppInfo *info)
{
  return info->server_installed_size;
}

gint64
eos_app_info_get_installed_size (const EosAppInfo *info)
{
  if (info->is_installed)
    {
      /* If we have this information in the keyfile, we assume it's accurate.
       * Return it as a fast-path.
       */
      if (info->info_installed_size > 0)
        return info->info_installed_size;

      /* If we have a cached computed size, return that. */
      if (info->computed_installed_size > 0)
        return info->computed_installed_size;

      /* Trigger size computation from the installation directory */
      compute_installed_size ((EosAppInfo *) info);
    }

  return 0;
}

gboolean
eos_app_info_is_installed (const EosAppInfo *info)
{
  return info->is_installed;
}

gboolean
eos_app_info_is_installable (const EosAppInfo *info)
{
  return !info->is_installed && info->is_available;
}

gboolean
eos_app_info_is_available (const EosAppInfo *info)
{
  return info->is_available;
}

gboolean
eos_app_info_is_updatable (const EosAppInfo *info)
{
  return info->is_installed && (info->info_filename != NULL) &&
    (eos_compare_versions (info->available_version,
                           info->installed_version) > 0);
}

gboolean
eos_app_info_is_updating (const EosAppInfo *info)
{
  return info->is_updating;
}

gboolean
eos_app_info_is_installing (const EosAppInfo *info)
{
  return info->is_installing;
}

gboolean
eos_app_info_is_removing (const EosAppInfo *info)
{
  return info->is_removing;
}

gboolean
eos_app_info_is_removable (const EosAppInfo *info)
{
  /* We can remove those applications that we have installed */
  return eos_app_info_is_store_installed (info);
}

gboolean
eos_app_info_is_store_installed (const EosAppInfo *info)
{
  return info->info_filename != NULL;
}

EosAppCategory
eos_app_info_get_category (const EosAppInfo *info)
{
  return info->category;
}

gboolean
eos_app_info_get_has_launcher (const EosAppInfo *info)
{
  return info->has_launcher && info->is_installed;
}

char *
eos_app_info_get_icon_name (const EosAppInfo *info)
{
  if (info->icon_name != NULL)
    return g_strdup (info->icon_name);

  /* TODO: for applications that are not on the system, just return
   * a hardcoded default for now. Eventually we want to get this information
   * from the server.
   */
  return g_strdup_printf ("eos-app-%s", eos_app_info_get_content_id (info));
}

EosAppState
eos_app_info_get_state (const EosAppInfo *info)
{
  EosAppState retval = EOS_APP_STATE_UNKNOWN;
  gboolean is_installed, is_installable, is_updatable, is_available;

  is_installed = eos_app_info_is_installed (info);
  is_updatable = eos_app_info_is_updatable (info);
  is_installable = eos_app_info_is_installable (info);
  is_available = eos_app_info_is_available (info);

  eos_app_log_debug_message ("%s (%p) "
                             "(installed: %s, updatable: %s,"
                             " installable: %s, available: %s)",
                             eos_app_info_get_application_id (info),
                             info,
                             is_installed ? "true" : "false",
                             is_updatable ? "true" : "false",
                             is_installable ? "true" : "false",
                             is_available ? "true" : "false");

  if (is_updatable)
    retval = EOS_APP_STATE_UPDATABLE;
  else if (is_installed)
    retval = EOS_APP_STATE_INSTALLED;
  else if (is_installable)
    retval = EOS_APP_STATE_AVAILABLE;

  return retval;
}

gint64
eos_app_info_get_installation_time (const EosAppInfo *info)
{
  return info->installation_time;
}

/**
 * eos_app_info_get_square_img:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_info_get_square_img (const EosAppInfo *info)
{
  if (info->square_img == NULL || info->square_img[0] == '\0')
    return NULL;

  return g_strdup_printf ("resource:///com/endlessm/appstore-content/apps/%s",
                          info->square_img);
}

/**
 * eos_app_info_get_featured_img:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_info_get_featured_img (const EosAppInfo *info)
{
  if (info->featured_img == NULL || info->featured_img[0] == '\0')
    return NULL;

  return g_strdup_printf ("resource:///com/endlessm/appstore-content/apps/%s",
                          info->featured_img);
}

guint
eos_app_info_get_n_screenshots (const EosAppInfo *info)
{
  return info->n_screenshots;
}

/**
 * eos_app_info_get_screenshots:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer full) (array zero-terminated=1): ...
 */
char **
eos_app_info_get_screenshots (const EosAppInfo *info)
{
  return g_strdupv (info->screenshots);
}

static EosFlexyShape
get_shape_from_id (const char *p)
{
  if (p == NULL || *p == '\0')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[0] != 'b')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[1] == '1' && p[2] == '\0')
    return EOS_FLEXY_SHAPE_SMALL;

  if (p[1] == '2')
    {
      if (p[2] == 'h' && p[3] == '\0')
        return EOS_FLEXY_SHAPE_MEDIUM_HORIZONTAL;

      if (p[2] == 'v' && p[3] == '\0')
        return EOS_FLEXY_SHAPE_MEDIUM_VERTICAL;
    }

  if (p[1] == '4' && p[2] == '\0')
    return EOS_FLEXY_SHAPE_LARGE;

  return EOS_FLEXY_SHAPE_SMALL;
}

static void
get_screenshots (JsonArray *array,
                 const char *language,
                 EosAppInfo *info)
{
  info->n_screenshots = json_array_get_length (array);
  info->screenshots = g_new0 (char *, info->n_screenshots + 1);

  for (guint i = 0; i < info->n_screenshots; i++)
    info->screenshots[i] = g_build_filename ("/com/endlessm/appstore-content/screenshots/",
                                             language,
                                             json_array_get_string_element (array, i),
                                             NULL);
}

static guint64
get_fs_available_space (const char *dir)
{
  GFile *current_directory = NULL;
  GFileInfo *filesystem_info = NULL;
  GError *error = NULL;

  /* Whatever FS we're on, check the space */
  if (dir == NULL)
    dir = ".";

  current_directory = g_file_new_for_path (dir);

  filesystem_info = g_file_query_filesystem_info (current_directory,
                                                  G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                                  NULL, /* Cancellable */
                                                  &error);

  g_object_unref (current_directory);

  if (error != NULL)
    {
      eos_app_log_error_message ("Could not retrieve available space: %s",
                                 error->message);
      g_error_free (error);

      /* Assume we have the space */
      return G_MAXUINT64;
    }

  guint64 available_space = g_file_info_get_attribute_uint64 (filesystem_info,
                                                              G_FILE_ATTRIBUTE_FILESYSTEM_FREE);

  eos_app_log_debug_message ("Available space: %" G_GUINT64_FORMAT, available_space);

  g_object_unref (filesystem_info);

  return available_space;
}

static gboolean
eos_app_info_get_has_sufficient_install_space (const EosAppInfo *info,
                                               const char       *dir)
{
  guint64 installed_size = 0;

  installed_size = eos_app_info_get_server_installed_size (info);

  eos_app_log_debug_message ("App %s installed size: %" G_GINT64_FORMAT,
                             eos_app_info_get_desktop_id (info),
                             installed_size);

  if (installed_size <= get_fs_available_space (dir))
    return TRUE;

  return FALSE;
}

gboolean
eos_app_info_check_install_space (const EosAppInfo *info)
{
  return eos_app_info_get_install_storage_type (info) != EOS_STORAGE_TYPE_UNKNOWN;
}

EosStorageType
eos_app_info_get_install_storage_type (const EosAppInfo *info)
{
  if (eos_has_secondary_storage () &&
      eos_app_info_get_has_sufficient_install_space (info, eos_get_secondary_storage ()))
    return EOS_STORAGE_TYPE_SECONDARY;

  if (eos_app_info_get_has_sufficient_install_space (info,  eos_get_primary_storage ()))
    return EOS_STORAGE_TYPE_PRIMARY;

  return EOS_STORAGE_TYPE_UNKNOWN;
}

EosStorageType
eos_app_info_get_storage_type (const EosAppInfo *info)
{
  return info->storage_type;
}

/**
 * eos_app_info_get_checksum:
 * @info:
 * @use_delta:
 * @error:
 *
 * ...
 *
 * Returns: (transfer none):
 */
const char *
eos_app_info_get_checksum (const EosAppInfo *info,
                           gboolean          use_delta,
                           GError          **error)
{
  const char *bundle_hash = NULL;

  if (use_delta)
    bundle_hash = eos_app_info_get_delta_bundle_hash (info);
  else
    bundle_hash = eos_app_info_get_bundle_hash (info);

  if (bundle_hash == NULL || *bundle_hash == '\0')
    {
      g_set_error (error, EOS_APP_STORE_ERROR,
                   EOS_APP_STORE_ERROR_CHECKSUM_MISSING,
                   _("No verification available for app '%s'"),
                   eos_app_info_get_title (info));
      return NULL;
    }

  return bundle_hash;
}

/*< private >
 * check_info_storage:
 * @info: the #EosAppInfo to update
 *
 * Updates file system related fields of @info.
 */
static void
check_info_storage (EosAppInfo *info)
{
  const char *external_storage_path = "/var/endless-extra";

  struct stat statbuf;
  if (stat (info->info_filename, &statbuf) < 0)
    return;

  /* We use second resolution for the installation time, because
   * nanosecond resolution is not interesting for us
   */
  info->installation_time = statbuf.st_ctim.tv_sec;

  /* We check if the application resides on a list of locations that correspond
   * to where the extra SD card storage could be mounted.
   */
  GFile *external_storage = g_file_new_for_path (external_storage_path);

  if (g_file_has_prefix (info->application_dir, external_storage))
    info->storage_type = EOS_STORAGE_TYPE_SECONDARY;
  else
    info->storage_type = EOS_STORAGE_TYPE_PRIMARY;

  g_object_unref (external_storage);
}

static gboolean
eos_app_info_installed_changed (EosAppInfo *info)
{
  GKeyFile *keyfile = g_key_file_new ();
  gboolean retval = FALSE;

  g_assert (info->info_filename != NULL);
  eos_app_log_debug_message ("Loading installed information for '%s' from '%s'",
                             info->application_id, info->info_filename);

  if (!g_key_file_load_from_file (keyfile, info->info_filename, 0, NULL))
    goto out;

#define GROUP   "Bundle"

  if (!g_key_file_has_group (keyfile, GROUP))
    goto out;

  eos_app_info_clear_installed_attributes (info);

  info->installed_version = g_key_file_get_string (keyfile, GROUP, FILE_KEYS[CODE_VERSION], NULL);
  info->installed_locale = g_key_file_get_string (keyfile, GROUP, FILE_KEYS[LOCALE], NULL);
  info->info_installed_size = g_key_file_get_int64 (keyfile, GROUP, FILE_KEYS[INSTALLED_SIZE], NULL);

  /* Bundles with an External group download additional content
   * from an external server, and thus the size of the bundle
   * reported in the .info file does not reflect the actual
   * installed size.  In that case, set the size here to 0
   * to force a later check of the actual installed size.
   */
  if (g_key_file_has_group (keyfile, "External"))
    info->info_installed_size = 0;

  check_info_storage (info);

  retval = TRUE;
  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);

#undef GROUP

out:
  g_key_file_unref (keyfile);

  return retval;
}

/*< private >*/
gboolean
eos_app_info_update_from_installed (EosAppInfo *info,
                                    const char *filename)
{
  g_clear_pointer (&info->info_filename, g_free);
  info->info_filename = g_strdup (filename);

  g_clear_object (&info->application_dir);

  GFile *info_file = g_file_new_for_path (filename);
  GFile *app_dir = g_file_get_parent (info_file);
  g_object_unref (info_file);

  GError *error = NULL;
  GFileInfo *file_info =
    g_file_query_info (app_dir,
                       G_FILE_ATTRIBUTE_STANDARD_IS_SYMLINK ","
                       G_FILE_ATTRIBUTE_STANDARD_SYMLINK_TARGET,
                       G_FILE_QUERY_INFO_NONE,
                       NULL, &error);

  if (error != NULL)
    {
      eos_app_log_error_message ("Could not retrieve install information "
                                 "for %s: %s",
                                 eos_app_info_get_desktop_id (info),
                                 error->message);
      g_error_free (error);
    }
  else
    {
      if (g_file_info_get_is_symlink (file_info))
        info->application_dir = g_file_resolve_relative_path
          (app_dir, g_file_info_get_symlink_target (file_info));

      g_object_unref (file_info);
    }

  if (info->application_dir == NULL)
    info->application_dir = g_object_ref (app_dir);

  g_object_unref (app_dir);

  return eos_app_info_installed_changed (info);
}

static gboolean
replace_string_field_from_json (JsonObject *obj,
                                int key_enum_index,
                                char **field)
{
  JsonNode *node = json_object_get_member (obj, JSON_KEYS[key_enum_index]);
  if (node != NULL)
    {
      g_free (*field);
      *field = json_node_dup_string (node);
      return TRUE;
    }

  return FALSE;
}

/*< private >*/
gboolean
eos_app_info_update_from_server (EosAppInfo *info,
                                 JsonObject *obj)
{
  if (!replace_string_field_from_json (obj, CODE_VERSION, &info->available_version))
    {
      eos_app_log_error_message ("Application data for '%s' is missing the "
                                 "required '%s' field.",
                                 eos_app_info_get_application_id (info),
                                 JSON_KEYS[CODE_VERSION]);
      return FALSE;
    }

  gboolean is_diff = FALSE;
  JsonNode *node = json_object_get_member (obj, JSON_KEYS[IS_DIFF]);
  if (node != NULL)
    is_diff = json_node_get_boolean (node);

  if (!is_diff)
    info->is_available = TRUE;

  node = json_object_get_member (obj, JSON_KEYS[INSTALLED_SIZE]);
  if (node != NULL)
    info->server_installed_size = json_node_get_int (node);

  node = json_object_get_member (obj, JSON_KEYS[SECONDARY_STORAGE]);
  if (node)
    info->for_secondary_storage = json_node_get_boolean (node);

  replace_string_field_from_json (obj, LOCALE, &info->server_locale);

  if (is_diff)
    {
      replace_string_field_from_json (obj, DOWNLOAD_LINK, &info->delta_bundle_uri);
      replace_string_field_from_json (obj, SIGNATURE_LINK, &info->delta_signature_uri);
      replace_string_field_from_json (obj, SHA_HASH, &info->delta_bundle_hash);
    }
  else
    {
      replace_string_field_from_json (obj, DOWNLOAD_LINK, &info->bundle_uri);
      replace_string_field_from_json (obj, SIGNATURE_LINK, &info->signature_uri);
      replace_string_field_from_json (obj, SHA_HASH, &info->bundle_hash);
    }

  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);

  return TRUE;
}

/*< private >*/
void
eos_app_info_update_from_gio (EosAppInfo *info,
                              GDesktopAppInfo *desktop_info)
{
  /* Do not update icon again if we already seen this desktop file
   * as a GIO override.
   */
  if (info->has_override)
    return;

  info->has_override = g_str_has_prefix (g_app_info_get_id (G_APP_INFO (desktop_info)),
                                         "eos-app-");

  g_free (info->icon_name);
  info->icon_name = g_desktop_app_info_get_string (desktop_info, G_KEY_FILE_DESKTOP_KEY_ICON);
}

/*< private >*/
void
eos_app_info_set_has_launcher (EosAppInfo *info,
                               gboolean has_launcher)
{
  info->has_launcher = has_launcher;
  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);
}

/*< private >*/
void
eos_app_info_set_is_installed (EosAppInfo *info,
                               gboolean is_installed)
{
  eos_app_log_debug_message ("Setting app '%s' as %sinstalled",
                             info->application_id,
                             is_installed ? "" : "not ");
  info->is_installed = is_installed;

  if (!is_installed)
    {
      eos_app_info_clear_installed_attributes (info);
      g_clear_pointer (&info->info_filename, g_free);
    }

  /* Reset removing flag if we are updating after uninstall */
  eos_app_info_set_is_removing (info, FALSE);

  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);
}

/*< private >*/
gboolean
eos_app_info_update_from_content (EosAppInfo *info,
                                  JsonObject *obj)
{
  if (json_object_has_member (obj, "title"))
    info->title = json_node_dup_string (json_object_get_member (obj, "title"));
  else
    info->title = g_strdup ("");

  if (json_object_has_member (obj, "subtitle"))
    info->subtitle = json_node_dup_string (json_object_get_member (obj, "subtitle"));
  else
    info->subtitle = g_strdup ("");

  if (json_object_has_member (obj, "description"))
    info->description = json_node_dup_string (json_object_get_member (obj, "description"));
  else
    info->description = g_strdup ("");

  if (json_object_has_member (obj, "displayShape"))
    {
      const char *shape = json_object_get_string_member (obj, "displayShape");

      info->shape = get_shape_from_id (shape); 
    }
  else
    info->shape = EOS_FLEXY_SHAPE_SMALL;

  if (json_object_has_member (obj, "square_img"))
    info->square_img = json_node_dup_string (json_object_get_member (obj, "square_img"));
  else
    info->square_img = NULL;

  if (json_object_has_member (obj, "featured_img"))
    info->featured_img = json_node_dup_string (json_object_get_member (obj, "featured_img"));
  else
    info->featured_img = NULL;

  /* FIXME: needs to be a boolean */
  if (json_object_has_member (obj, "is_featured") &&
      json_object_get_boolean_member (obj, "is_featured"))
    info->is_featured = TRUE;
  else
    info->is_featured = FALSE;

  /* FIXME: needs to be a boolean */
  if (json_object_has_member (obj, "is_offline") &&
      json_object_get_boolean_member (obj, "is_offline"))
    info->is_offline = TRUE;
  else
    info->is_offline = FALSE;

  if (json_object_has_member (obj, "category"))
    {
      const char *category = json_object_get_string_member (obj, "category");

      info->category = eos_app_category_from_id (category);
    }
  else
    info->category = EOS_APP_CATEGORY_UTILITIES;

  if (json_object_has_member (obj, "screenshots"))
    {
      JsonNode *node = json_object_get_member (obj, "screenshots");

      if (JSON_NODE_HOLDS_OBJECT (node))
        {
          JsonObject *screenshots = json_node_get_object (node);
          const gchar * const * my_languages = g_get_language_names ();
          gchar *language = NULL;

          for (gint i = 0; my_languages[i] != NULL; i++)
            {
              gchar *my_language = g_ascii_strdown (my_languages[i], -1);

              if (json_object_has_member (screenshots, my_language))
                {
                  language = my_language;
                  break;
                }

              g_free (my_language);
            }

          if (!language)
            language = g_strdup ("C");

          JsonNode *array = json_object_get_member (screenshots, language);
          if (array != NULL)
            get_screenshots (json_node_get_array (array), language, info);
          g_free (language);
        }
    }
  else
    info->n_screenshots = 0;

  return TRUE;
}

/*< private >*/
void
eos_app_info_set_is_installing (EosAppInfo *info,
                                gboolean is_installing)
{
  info->is_installing = is_installing;
  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);
}

/*< private >*/
void
eos_app_info_set_is_removing (EosAppInfo *info,
                              gboolean is_removing)
{
  info->is_removing = is_removing;
  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);
}

/*< private >*/
void
eos_app_info_set_is_updating (EosAppInfo *info,
                              gboolean is_updating)
{
  info->is_updating = is_updating;
  g_object_notify_by_pspec (G_OBJECT (info), properties[PROP_STATE]);
}

/*< private >*/
void
eos_app_info_emit_download_progress (EosAppInfo *info,
                                     goffset     current,
                                     goffset     total)
{
  g_signal_emit (info, eos_app_info_signals[DOWNLOAD_PROGRESS], 0,
                 current, total);
}
