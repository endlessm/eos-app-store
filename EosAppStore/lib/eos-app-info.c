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

EosAppInfo *
eos_app_info_new (const char *application_id)
{
  EosAppInfo *info = g_slice_new0 (EosAppInfo);

  info->shape = EOS_FLEXY_SHAPE_SMALL;
  info->ref_count = 1;

  info->application_id = g_strdup (application_id);
  info->desktop_id = g_strdup_printf ("%s.desktop", info->application_id);

  return info;
}

EosAppInfo *
eos_app_info_ref (EosAppInfo *info)
{
  if (info == NULL)
    return NULL;

  g_atomic_int_inc (&(info->ref_count));

  return info;
}

void
eos_app_info_unref (EosAppInfo *info)
{
  if (info == NULL)
    return;

  if (g_atomic_int_dec_and_test (&(info->ref_count)))
    {
      g_free (info->application_id);
      g_free (info->desktop_id);
      g_free (info->title);
      g_free (info->subtitle);
      g_free (info->description);
      g_free (info->square_img);
      g_free (info->featured_img);
      g_free (info->version);
      g_free (info->locale);
      g_free (info->bundle_uri);
      g_free (info->signature_uri);
      g_free (info->bundle_hash);
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

const char *
eos_app_info_get_desktop_id (const EosAppInfo *info)
{
  return info->desktop_id;
}

const char *
eos_app_info_get_application_id (const EosAppInfo *info)
{
  return info->application_id;
}

const char *
eos_app_info_get_description (const EosAppInfo *info)
{
  return g_dpgettext2 (CONTENT_GETTEXT_PACKAGE, "description", info->description);
}

const char *
eos_app_info_get_version (const EosAppInfo *info)
{
  return info->version;
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
eos_app_info_is_installable (const EosAppInfo *info)
{
  return !info->is_installed && info->is_available;
}

gboolean
eos_app_info_is_updatable (const EosAppInfo *info)
{
  return info->update_available;
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
  if (info == NULL || info->square_img == NULL || info->square_img[0] == '\0')
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
  if (info == NULL || info->featured_img == NULL || info->featured_img[0] == '\0')
    return NULL;

  return g_strdup_printf ("resource:///com/endlessm/appstore-content/apps/%s",
                          info->featured_img);
}

guint
eos_app_info_get_n_screenshots (const EosAppInfo *info)
{
  if (info == NULL)
    return 0;

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

/* Keep in the same order as the EosAppCategory enumeration */
static const struct {
  const EosAppCategory category;
  const char *id;
} categories[] = {
  /* Translators: use the same string used to install the app store content JSON */
  { EOS_APP_CATEGORY_EDUCATION,     N_("Education") },
  { EOS_APP_CATEGORY_GAMES,         N_("Games") },
  { EOS_APP_CATEGORY_RESOURCES,     N_("Resources") },
  { EOS_APP_CATEGORY_UTILITIES,     N_("Utilities") },
};

static const guint n_categories = G_N_ELEMENTS (categories);

static EosAppCategory
get_category_from_id (const char *p)
{
  guint i;

  if (p == NULL || *p == '\0')
    return EOS_APP_CATEGORY_UTILITIES;

  for (i = 0; i < n_categories; i++)
    {
      if (strcmp (categories[i].id, p) == 0)
        return categories[i].category;
    }

  return EOS_APP_CATEGORY_UTILITIES;
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

  N_KEYS
};

/*< private >
 * check_secondary_storage:
 * @filename: the full path to the bundle info file
 *
 * Returns: %TRUE if the bundle info resides on secondary storage
 */
static gboolean
check_secondary_storage (const char *filename)
{
  /* we check if the file resides on a volume mounted using overlayfs.
   * this is a bit more convoluted; in theory, we could check if the
   * directory in which @filename is located has the overlayfs magic
   * bit, but that bit is not exposed by the kernel headers, so we would
   * have to do assume that the overlayfs magic bit never changes.
   */
  struct stat statbuf;
  if (stat (filename, &statbuf) < 0)
    return FALSE;

  dev_t file_stdev = statbuf.st_dev;

  /* and we compare them with the same fields of a list of known
   * mount points
   */
  const char *known_mount_points[] = {
    "/var/endless-extra",
  };

  for (int i = 0; i < G_N_ELEMENTS (known_mount_points); i++)
   {
      if (stat (known_mount_points[i], &statbuf) < 0)
        return FALSE;

      if (file_stdev == statbuf.st_dev)
        return TRUE;
    }

  return FALSE;
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

  g_free (info->version);
  info->version = g_key_file_get_string (keyfile, GROUP, FILE_KEYS[CODE_VERSION], NULL);

  g_free (info->locale);
  info->locale = g_key_file_get_string (keyfile, GROUP, FILE_KEYS[LOCALE], NULL);

  info->installed_size = g_key_file_get_int64 (keyfile, GROUP, FILE_KEYS[INSTALLED_SIZE], NULL);

  if (g_key_file_has_key (keyfile, GROUP, FILE_KEYS[SECONDARY_STORAGE], NULL))
    info->on_secondary_storage = g_key_file_get_boolean (keyfile, GROUP, FILE_KEYS[SECONDARY_STORAGE], NULL);
  else
    info->on_secondary_storage = check_secondary_storage (filename);

  /* If we found it here, then it's installed */
  info->is_installed = TRUE;

  retval = TRUE;

#undef GROUP

out:
  g_key_file_unref (keyfile);

  return retval;
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

  JsonNode *node = json_object_get_member (obj, JSON_KEYS[CODE_VERSION]);
  if (node != NULL)
    {
      const char *version = json_node_get_string (node);
      int version_cmp = eos_compare_versions (info->version, version);

      /* If the server returns a newer version, we update the related fields;
       * otherwise, we keep what we have
       */
      if (version_cmp > 0)
        return FALSE;

      if (version_cmp < 0)
        {
          g_free (info->version);
          info->version = g_strdup (version);

          /* Newer version means we have an update */
          info->update_available = TRUE;
        }
    }
  else
    {
      eos_app_log_error_message ("Application data for '%s' is missing the "
                                 "required '%s' field.",
                                 eos_app_info_get_application_id (info),
                                 JSON_KEYS[CODE_VERSION]);
      return FALSE;
    }

  /* If we found it here, then it's available */
  info->is_available = TRUE;

  node = json_object_get_member (obj, JSON_KEYS[LOCALE]);
  if (node != NULL)
    {
      g_free (info->locale);
      info->locale = json_node_dup_string (node);
    }

  node = json_object_get_member (obj, JSON_KEYS[INSTALLED_SIZE]);
  if (node != NULL)
    info->installed_size = json_node_get_int (node);

  node = json_object_get_member (obj, JSON_KEYS[SECONDARY_STORAGE]);
  if (node)
    info->on_secondary_storage = json_node_get_boolean (node);

  node = json_object_get_member (obj, JSON_KEYS[DOWNLOAD_LINK]);
  if (node != NULL)
    {
      g_free (info->bundle_uri);
      info->bundle_uri = json_node_dup_string (node);
    }

  node = json_object_get_member (obj, JSON_KEYS[SIGNATURE_LINK]);
  if (node != NULL)
    {
      g_free (info->signature_uri);
      info->signature_uri = json_node_dup_string (node);
    }

  node = json_object_get_member (obj, JSON_KEYS[SHA_HASH]);
  if (node != NULL)
    {
      g_free (info->bundle_hash);
      info->bundle_hash = json_node_dup_string (node);
    }

  return TRUE;
}

/*< private >*/
EosAppInfo *
eos_app_info_create_from_content (JsonNode *node)
{
  const char *app_id;

  if (!JSON_NODE_HOLDS_OBJECT (node))
    return NULL;

  JsonObject *obj = json_node_get_object (node);
  if (!json_object_has_member (obj, "application-id"))
    return NULL;

  app_id = json_object_get_string_member (obj, "application-id");

  EosAppInfo *info = eos_app_info_new (app_id);

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

      info->category = get_category_from_id (category);
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

  return info;
}
