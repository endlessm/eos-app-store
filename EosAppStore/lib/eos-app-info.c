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

G_DEFINE_BOXED_TYPE (EosAppInfo, eos_app_info, eos_app_info_ref, eos_app_info_unref)

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
  "fromVersion",
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
  FROM_VERSION,
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

EosAppInfo *
eos_app_info_new (const char *application_id)
{
  EosAppInfo *info = g_slice_new0 (EosAppInfo);

  info->shape = EOS_FLEXY_SHAPE_SMALL;
  info->ref_count = 1;

  info->application_id = g_strdup (application_id);
  info->content_id = content_id_from_application_id (application_id);
  info->desktop_id = g_strdup_printf ("%s.desktop", info->application_id);

  info->installation_time = -1;

  return info;
}

EosAppInfo *
eos_app_info_new_from_server_json (JsonNode *root)
{
  if (!JSON_NODE_HOLDS_OBJECT (root))
    {
      eos_app_log_error_message ("Application data malformed.");
      return NULL;
    }

  JsonObject *obj = json_node_get_object (root);

  JsonNode *node;

  EosAppInfo *info = NULL;

  node = json_object_get_member (obj, JSON_KEYS[APP_ID]);
  if (node)
    {
      const char *app_id = json_node_get_string (node);
      info = eos_app_info_new (app_id);
    }
  else
    {
      eos_app_log_error_message ("Application data is missing the "
                                 "required '%s' field.",
                                 JSON_KEYS[APP_ID]);

      return NULL;
    }

  if (!eos_app_info_update_from_server (info, root))
    {
      eos_app_info_unref (info);
      return NULL;
    }

  return info;
}

EosAppInfo *
eos_app_info_ref (EosAppInfo *info)
{
  g_atomic_int_inc (&(info->ref_count));

  return info;
}

void
eos_app_info_clear_server_update_attributes (EosAppInfo *info)
{
  g_clear_pointer (&info->locale, g_free);

  g_clear_pointer (&info->available_version, g_free);

  g_clear_pointer (&info->bundle_uri, g_free);
  g_clear_pointer (&info->signature_uri, g_free);
  g_clear_pointer (&info->bundle_hash, g_free);

  g_clear_pointer (&info->delta_bundle_uri, g_free);
  g_clear_pointer (&info->delta_signature_uri, g_free);
  g_clear_pointer (&info->delta_bundle_hash, g_free);

  /* Meta fields that need clearing */
  info->update_available = FALSE;
  info->is_available = FALSE;
}

void
eos_app_info_unref (EosAppInfo *info)
{
  if (g_atomic_int_dec_and_test (&(info->ref_count)))
    {
      g_free (info->application_id);
      g_free (info->desktop_id);
      g_free (info->content_id);
      g_free (info->title);
      g_free (info->subtitle);
      g_free (info->description);
      g_free (info->square_img);
      g_free (info->featured_img);
      g_free (info->locale);

      g_free (info->installed_version);

      eos_app_info_clear_server_update_attributes (info);

      g_free (info->icon_name);
      g_strfreev (info->screenshots);

      g_slice_free (EosAppInfo, info);
    }
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
  return info->locale;
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
eos_app_info_is_featured (const EosAppInfo *info)
{
  return info->is_featured;
}

gboolean
eos_app_info_is_offline (const EosAppInfo *info)
{
  return info->is_offline;
}

gboolean
eos_app_info_is_on_secondary_storage (const EosAppInfo *info)
{
  return info->on_secondary_storage;
}

gint64
eos_app_info_get_installed_size (const EosAppInfo *info)
{
  return info->installed_size;
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
eos_app_info_is_updatable (const EosAppInfo *info)
{
  return info->is_installed && info->update_available;
}

gboolean
eos_app_info_is_removable (const EosAppInfo *info)
{
  return !info->on_secondary_storage;
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
  gboolean is_installed, is_installable, is_updatable;

  is_installed = eos_app_info_is_installed (info);
  is_updatable = eos_app_info_is_updatable (info);
  is_installable = eos_app_info_is_installable (info);

  eos_app_log_debug_message ("%s (%p)"
                             "(installed: %s, updatable: %s, installable: %s",
                             eos_app_info_get_application_id (info),
                             info,
                             is_installed ? "true" : "false",
                             is_updatable ? "true" : "false",
                             is_installable ? "true" : "false");

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

  char *path = eos_app_get_content_dir ();

  for (guint i = 0; i < info->n_screenshots; i++)
    info->screenshots[i] = g_build_filename (path,
                                             "resources",
                                             "screenshots",
                                             language,
                                             json_array_get_string_element (array, i),
                                             NULL);

  g_free (path);
}

static guint64
get_fs_available_space (void)
{
  GFile *current_directory = NULL;
  GFileInfo *filesystem_info = NULL;
  GError *error = NULL;

  /* Whatever FS we're on, check the space */
  current_directory = g_file_new_for_path (".");

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

gboolean
eos_app_info_get_has_sufficient_install_space (const EosAppInfo *info)
{
  guint64 installed_size = 0;

  installed_size = eos_app_info_get_installed_size (info);

  eos_app_log_debug_message ("App %s installed size: %" G_GINT64_FORMAT,
                             eos_app_info_get_desktop_id (info),
                             installed_size);

  if (installed_size <= get_fs_available_space ())
    return TRUE;

  return FALSE;
}

/* Keep this list updated with the locations we use for
 * installing app bundles
 */
static const char *known_mount_points[] = {
  "/var/endless-extra",
};

/*< private >
 * check_info_storage:
 * @info: the #EosAppInfo to update
 * @filename: the full path to the bundle info file
 *
 * Updates file system related fields of @info.
 */
static void
check_info_storage (EosAppInfo *info,
                    const char *filename)
{
  /* Default values */
  info->on_secondary_storage = FALSE;
  info->installation_time = -1;

  /* we check if the file resides on a volume mounted using overlayfs.
   * this is a bit more convoluted; in theory, we could check if the
   * directory in which @filename is located has the overlayfs magic
   * bit, but that bit is not exposed by the kernel headers, so we would
   * have to do assume that the overlayfs magic bit never changes.
   */
  struct stat statbuf;
  if (stat (filename, &statbuf) < 0)
    return;

  /* We use second resolution for the installation time, because
   * nanosecond resolution is not interesting for us
   */
  info->installation_time = statbuf.st_ctim.tv_sec;

  dev_t file_stdev = statbuf.st_dev;

  /* and we compare them with the same fields of a list of known
   * mount points
   */
  for (int i = 0; i < G_N_ELEMENTS (known_mount_points); i++)
   {
      if (stat (known_mount_points[i], &statbuf) < 0)
        break;

      if (file_stdev == statbuf.st_dev)
        {
          info->on_secondary_storage = TRUE;
          break;
        }
    }
}

/*< private >*/
gboolean
eos_app_info_update_from_installed (EosAppInfo *info,
                                    const char *filename)
{
  GKeyFile *keyfile = g_key_file_new ();
  gboolean retval = FALSE;

  if (!g_key_file_load_from_file (keyfile, filename, 0, NULL))
    goto out;

#define GROUP   "Bundle"

  if (!g_key_file_has_group (keyfile, GROUP))
    goto out;

  g_free (info->installed_version);
  info->installed_version = g_key_file_get_string (keyfile, GROUP,
                                                   FILE_KEYS[CODE_VERSION],
                                                   NULL);

  g_free (info->locale);
  info->locale = g_key_file_get_string (keyfile, GROUP, FILE_KEYS[LOCALE], NULL);

  info->installed_size = g_key_file_get_int64 (keyfile, GROUP, FILE_KEYS[INSTALLED_SIZE], NULL);

  check_info_storage (info, filename);

  /* Data coming from the keyfile takes precedence */
  if (g_key_file_has_key (keyfile, GROUP, FILE_KEYS[SECONDARY_STORAGE], NULL))
    info->on_secondary_storage = g_key_file_get_boolean (keyfile, GROUP, FILE_KEYS[SECONDARY_STORAGE], NULL);

  /* If we found it here, then it's installed */
  eos_app_log_debug_message ("Setting app '%s' as installed",
                             info->application_id);
  info->is_installed = TRUE;

  retval = TRUE;

#undef GROUP

out:
  g_key_file_unref (keyfile);

  return retval;
}

static void
replace_string_field_from_json (JsonObject *obj,
                                int key_enum_index,
                                char **field)
{
  JsonNode *node = json_object_get_member (obj, JSON_KEYS[key_enum_index]);
  if (node != NULL)
    {
      g_free (*field);
      *field = json_node_dup_string (node);
    }
}

/*< private >*/
gboolean
eos_app_info_update_from_server (EosAppInfo *info,
                                 JsonNode *root)
{
  if (!JSON_NODE_HOLDS_OBJECT (root))
    {
      eos_app_log_error_message ("Application data for '%s' is malformed.",
                                 eos_app_info_get_application_id (info));
      return FALSE;
    }

  JsonObject *obj = json_node_get_object (root);

  JsonNode *node;

  gboolean is_diff = FALSE;
  node = json_object_get_member (obj, JSON_KEYS[IS_DIFF]);
  if (node != NULL)
    {
      /* TODO: This needs checks to compare against local version */
      is_diff = json_node_get_boolean (node);
      if (is_diff)
        info->update_available = TRUE;
      else
        info->is_available = TRUE;
    }

  node = json_object_get_member (obj, JSON_KEYS[CODE_VERSION]);
  if (node != NULL)
    {
      g_free (info->available_version);
      info->available_version = json_node_dup_string (node);
    }
  else
    {
      eos_app_log_error_message ("Application data for '%s' is missing the "
                                 "required '%s' field.",
                                 eos_app_info_get_application_id (info),
                                 JSON_KEYS[CODE_VERSION]);
      return FALSE;
    }

  node = json_object_get_member (obj, JSON_KEYS[INSTALLED_SIZE]);
  if (node != NULL)
    info->installed_size = json_node_get_int (node);

  node = json_object_get_member (obj, JSON_KEYS[SECONDARY_STORAGE]);
  if (node)
    info->on_secondary_storage = json_node_get_boolean (node);

  replace_string_field_from_json (obj, LOCALE, &info->locale);

  if (!is_diff)
    {
      replace_string_field_from_json (obj, DOWNLOAD_LINK, &info->bundle_uri);
      replace_string_field_from_json (obj, SIGNATURE_LINK, &info->signature_uri);
      replace_string_field_from_json (obj, SHA_HASH, &info->bundle_hash);
    }
  else
    {
      replace_string_field_from_json (obj, DOWNLOAD_LINK, &info->delta_bundle_uri);
      replace_string_field_from_json (obj, SIGNATURE_LINK, &info->delta_signature_uri);
      replace_string_field_from_json (obj, SHA_HASH, &info->delta_bundle_hash);
    }

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
}

/*< private >*/
gboolean
eos_app_info_update_from_content (EosAppInfo *info,
                                  JsonNode *node)
{
  if (!JSON_NODE_HOLDS_OBJECT (node))
    return FALSE;

  JsonObject *obj = json_node_get_object (node);

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
