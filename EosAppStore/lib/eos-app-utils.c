/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"

#include "eos-app-enums.h"
#include "eos-app-log.h"
#include "eos-link-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <glib/gstdio.h>
#include <json-glib/json-glib.h>
#include <errno.h>

#define APP_STORE_CONTENT_LINKS "links"

#define BUNDLE_DIR              LOCALSTATEDIR "/tmp/eos-app-store"
#define DOWNLOAD_DIR_PREFIX     "dl"
#define APP_DIR_DEFAULT         "/endless"

G_DEFINE_QUARK (eos-app-utils-error-quark, eos_app_utils_error)

char *
eos_get_bundle_download_dir (const char *app_id,
                             const char *version)
{
  char *download_dir = g_strdup_printf ("%s%u_%s_%s",
                                        DOWNLOAD_DIR_PREFIX,
                                        getuid (),
                                        app_id,
                                        version);

  char *target_dir = g_build_filename (BUNDLE_DIR, download_dir, NULL);
  g_free (download_dir);

  if (g_mkdir_with_parents (target_dir, 0755) != 0)
    {
      int saved_errno = errno;
      eos_app_log_error_message ("Unable to create temporary directory: %s",
                                 g_strerror (saved_errno));
    }

  g_chmod (BUNDLE_DIR, 01777);

  eos_app_log_info_message ("Target dir: %s", target_dir);

  return target_dir;
}

const char *
eos_get_os_personality (void)
{
  static char *personality;

  if (g_once_init_enter (&personality))
    {
      gchar *tmp;

      tmp = g_strdup (g_getenv ("ENDLESS_OS_PERSONALITY"));
      if (tmp != NULL && tmp[0] == '\0')
        {
          g_free (tmp);
          tmp = NULL;
        }

      if (tmp == NULL)
        {
          GKeyFile *personality_file = g_key_file_new ();
          char *path = g_build_filename (SYSCONFDIR,
                                         "EndlessOS",
                                         "personality.conf",
                                         NULL);

          GError *error = NULL;
          g_key_file_load_from_file (personality_file, path,
                                     G_KEY_FILE_NONE, &error);

          if (error == NULL)
            tmp = g_key_file_get_string (personality_file, "Personality",
                                         "PersonalityName", &error);

          if (error != NULL)
            {
              g_critical ("No personality defined: %s", error->message);
              g_error_free (error);
              tmp = NULL;
            }

          g_key_file_free (personality_file);
          g_free (path);
        }

      if (tmp == NULL)
        tmp = g_strdup ("default");

      eos_app_log_info_message ("Personality: %s", tmp);

      g_once_init_leave (&personality, tmp);
    }

  return personality;
}

const char *
eos_get_cache_dir (void)
{
  static char *download_url;

  if (g_once_init_enter (&download_url))
    {
      char *tmp = g_build_filename (g_get_user_cache_dir (), "com.endlessm.AppStore", NULL);

      eos_app_log_info_message ("Download dir: %s", tmp);

      g_once_init_leave (&download_url, tmp);
    }

  return download_url;
}

const char *
eos_get_bundles_dir (void)
{
  return eos_app_manager_get_applications_dir (eos_get_eam_dbus_proxy ());
}

gboolean
eos_has_secondary_storage (void)
{
  const char *primary_storage, *secondary_storage;

  primary_storage = eos_get_primary_storage ();
  secondary_storage = eos_get_secondary_storage ();

  /* The secondary storage path does not exist */
  struct stat secondary_statbuf;
  if (stat (secondary_storage, &secondary_statbuf) < 0)
    return FALSE;

  /* If the primary storage path does not exist, we're screwed.
   * Throw an assertion instead of continuing in a corrupted
   * state.
   */
  struct stat primary_statbuf;
  if (stat (primary_storage, &primary_statbuf) < 0)
    g_assert_not_reached ();

  /* We have a valid secondary storage if it's on a different
   * device than the primary.
   */
  return primary_statbuf.st_dev != secondary_statbuf.st_dev;
}

const char *
eos_get_primary_storage (void)
{
  return eos_app_manager_get_primary_storage (eos_get_eam_dbus_proxy ());
}

const char *
eos_get_secondary_storage (void)
{
  return eos_app_manager_get_secondary_storage (eos_get_eam_dbus_proxy ());
}

const char *
eos_get_storage_path_for_type (EosStorageType storage_type)
{
  switch (storage_type)
    {
    case EOS_STORAGE_TYPE_UNKNOWN:
      return NULL;

    case EOS_STORAGE_TYPE_PRIMARY:
      return eos_get_primary_storage ();

    case EOS_STORAGE_TYPE_SECONDARY:
      return eos_get_secondary_storage ();
    }

  g_assert_not_reached ();

  return NULL;
}

gboolean
eos_use_delta_updates (void)
{
  return eos_app_manager_get_enable_delta_updates (eos_get_eam_dbus_proxy ());
}

const char *
eos_get_app_server_url (void)
{
  return eos_app_manager_get_server_url (eos_get_eam_dbus_proxy ());
}

static const char *
eos_get_app_server_api (void)
{
  return eos_app_manager_get_api_version (eos_get_eam_dbus_proxy ());
}

/*
 * Parse the /etc/os-release file if present:
 * http://www.freedesktop.org/software/systemd/man/os-release.html
 */
static gboolean
parse_os_release_file (gchar  **version_id,
                       GError **error)
{
  char *contents = NULL;
  char **lines;
  gint idx;

  if (!g_file_get_contents (SYSCONFDIR "/os-release", &contents, NULL, error))
    return FALSE;

  lines = g_strsplit (contents, "\n", -1);
  g_free (contents);

  gboolean ret = FALSE;

  for (idx = 0; lines[idx] != NULL; idx++)
    {
      char *line = lines[idx];

      line = g_strstrip (line);

      if (!g_str_has_prefix (line, "VERSION_ID"))
        continue;

      char *p = strchr (line, '=');
      if (p == NULL)
        continue;

      p += 1;
      if (p == '\0')
        continue;

      while (g_ascii_isspace (*p) || *p == '"')
        p++;

      char *start = p;
      if (p == '\0')
        continue;

      while (*p != '"' && *p != '\0')
        p++;

      *version_id = g_strndup (start, p - start);
      ret = TRUE;
      break;
    }

  g_strfreev (lines);

  return ret;
}

const char *
eos_get_os_version (void)
{
  static char *os_version;

  if (g_once_init_enter (&os_version))
    {
      char *tmp = NULL;

      GError *error = NULL;
      parse_os_release_file (&tmp, &error);
      if (error != NULL)
        {
          eos_app_log_error_message ("Cannot parse os-release file: %s", error->message);
          g_error_free (error);

          tmp = g_strdup ("1.0");
        }

      eos_app_log_info_message ("OS Version: %s", tmp);

      g_once_init_leave (&os_version, tmp);
    }

  return os_version;
}

static const char *
get_os_arch (void)
{
  /* Defined at configure time */
  return EOS_ARCH;
}

static const char *
eos_link_get_category_name (EosLinkCategory category)
{
  switch (category)
    {
    case EOS_LINK_CATEGORY_NEWS:
      return "News";

    case EOS_LINK_CATEGORY_SPORTS:
      return "Sports";

    case EOS_LINK_CATEGORY_EDUCATION:
      return "Education and Health";

    case EOS_LINK_CATEGORY_ENTERTAINMENT:
      return "Entertainment";

    case EOS_LINK_CATEGORY_LOCAL:
      return "Local";

    default:
      return "";
    }
}

JsonArray *
eos_app_parse_resource_content (const char *content_type,
                                const char *content_name,
                                GError **error_out)
{
  gint64 start_time = g_get_monotonic_time ();
  JsonArray *content_array = NULL;
  GError *error = NULL;
  JsonParser *parser = json_parser_new ();

  char *content_file = g_strdup_printf ("/com/endlessm/appstore-content/%s/%s.json",
                                        content_type, content_name);

  GBytes *data = g_resources_lookup_data (content_file, 0, &error);
  if (error != NULL)
    {
      g_debug ("Unable to load content from '%s': %s", content_file, error->message);
      g_propagate_error (error_out, error);
      goto out_error;
    }

  json_parser_load_from_data (parser,
                              g_bytes_get_data (data, NULL),
                              g_bytes_get_size (data),
                              &error);

  if (error != NULL)
    {
      g_critical ("Unable to load content from '%s': %s", content_file, error->message);
      g_propagate_error (error_out, error);
      goto out_error;
    }

  JsonNode *node = json_parser_get_root (parser);
  g_assert (JSON_NODE_HOLDS_ARRAY (node));

  content_array = json_node_dup_array (node);

  eos_app_log_debug_message ("Content type '%s' loading: %.3f msecs",
                             content_type,
                             (double) (g_get_monotonic_time () - start_time) / 1000);

 out_error:
  g_object_unref (parser);
  g_free (content_file);

  return content_array;
}

/**
 * eos_link_load_content:
 *
 * ...
 *
 * Returns: (element-type EosLinkInfo) (transfer full): ...
 */
GList *
eos_link_load_content (EosLinkCategory category)
{
  GList *links = NULL;
  JsonNode *element;
  JsonObject *obj;
  const gchar *category_name;

  static JsonArray *categories_array = NULL;
  const char * const *language_names = g_get_language_names ();
  int idx = 0;

  /* Find the content that is the best match for the user's language. */
  while (!categories_array && language_names[idx] != NULL)
    {
      categories_array = eos_app_parse_resource_content (APP_STORE_CONTENT_LINKS, language_names[idx], NULL);
      idx++;
    }

  if (categories_array == NULL)
    return NULL;

  guint i, n_elements = json_array_get_length (categories_array);

  /* First contents are the categories; search for the interested one */
  category_name = eos_link_get_category_name (category);
  for (i = 0; i < n_elements; i++)
    {
      element = json_array_get_element (categories_array, i);
      if (!JSON_NODE_HOLDS_OBJECT (element))
        continue;

      obj = json_node_get_object (element);

      if (strcmp (json_node_get_string (json_object_get_member (obj, "category")), category_name) == 0)
        break;
    }

  if (i >= n_elements)
    {
      eos_app_log_info_message ("Unable to find category '%s'", category_name);
      goto out;
    }

  element = json_object_get_member (obj, "links");

  if (!JSON_NODE_HOLDS_ARRAY (element))
    {
      g_critical ("Category '%s' does not contain an array", category_name);
      goto out;
    }

  JsonArray *links_array = json_node_get_array (element);
  n_elements = json_array_get_length (links_array);

  for (i = 0; i < n_elements; i++)
    {
      element = json_array_get_element (links_array, i);
      EosLinkInfo *info = eos_link_info_create_from_json (element);
      if (info != NULL)
        links = g_list_prepend (links, info);
    }

out:
  return g_list_reverse (links);
}

void
eos_app_load_screenshot (GtkWidget  *image,
                         const char *resource_path,
                         int         width)
{
  GError *error = NULL;
  GdkPixbuf *pixbuf =
    gdk_pixbuf_new_from_resource_at_scale (resource_path, width, -1, TRUE, &error);

  if (error != NULL)
    {
      g_warning ("Cannot load image at path '%s': %s", resource_path, error->message);
      g_error_free (error);
      gtk_widget_hide (image);
      return;
    }

  gtk_image_set_from_pixbuf (GTK_IMAGE (image), pixbuf);
  gtk_widget_show (image);

  g_object_unref (pixbuf);
}

/**
 * eos_link_get_favicon:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
GdkPixbuf *
eos_link_get_favicon (WebKitWebView *webview)
{
  GdkPixbuf *dest;
  cairo_surface_t *icon_surface = webkit_web_view_get_favicon (webview);

  if (icon_surface == NULL)
    return NULL;

  gint favicon_width = cairo_image_surface_get_width (icon_surface);
  gint favicon_height = cairo_image_surface_get_height (icon_surface);
  gint biggest =  MAX (favicon_width, favicon_height);
  gdouble scale = 1.0;
  gdouble offset_x = 0.0;
  gdouble offset_y = 0.0;
  GdkPixbuf *base = NULL;
  GdkPixbuf *mask = NULL;

  if (biggest > 64)
    {
      /* If size is > 64px, resize it to 64px
         and mask to a 60px square with rounded corners
         (resize to 64px prior to masking rather
         than resize directly to 60px, in order to reduce
         the likelihood of artifacts, for instance if
         the original is 128px) */
      scale = (gdouble) 64 / biggest;
      mask = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_big-icon.png", NULL);
    }
  else if (biggest >= 60)
    {
      /* If size is in range [60px, 64px],
         use the icon without resizing, but center within the canvas
         and mask to a 60px square with rounded corners */
      mask = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_big-icon.png", NULL);
    }
  else if (biggest >= 48)
    {
      /* If size is in range [48px, 60px),
         resize to 48px and center within the placeholder icon */
      scale = (gdouble) 48 / biggest;
      base = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_big-icon.png", NULL);
    }
  else if (biggest > 16)
    {
      /* If size is in range (16px, 48px),
         use the icon without resizing,
         but center within the placeholder icon */
      base = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_big-icon.png", NULL);
    }
  else
    {
      /* Otherwise, if size is <= 16 px,
         use the icon without resizing;
         but, as the holder for the icon
         in the shell is 64x64,
         and the shell scales the desktop icons,
         let's put the icon inside a canvas of 64x64,
         so the shell does not scale it */
      base = gdk_pixbuf_new_from_resource ("/com/endlessm/appstore/generic-link_favicon.png", NULL);
    }

  /* Scale each dimension to resize */
  favicon_width *= scale;
  favicon_height *= scale;

  /* Center the icon within its canvas */
  offset_x = (64 - favicon_width) / 2;
  offset_y = (64 - favicon_height) / 2;

  cairo_surface_t *dest_surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, 64, 64);
  cairo_t *cr = cairo_create (dest_surface);

  if (base != NULL)
    {
      /* Paint the icon on top of a base pixbuf */
      gdk_cairo_set_source_pixbuf (cr, base, 0, 0);
      cairo_paint (cr);
      g_object_unref (base);
    }

  cairo_pattern_t *icon_pattern = cairo_pattern_create_for_surface (icon_surface);
  cairo_matrix_t matrix;

  cairo_matrix_init_scale (&matrix, 1.0 / scale, 1.0 / scale);
  cairo_matrix_translate (&matrix, - offset_x, - offset_y);
  cairo_pattern_set_matrix (icon_pattern, &matrix);

  cairo_set_source (cr, icon_pattern);

  if (mask != NULL)
    {
      /* Use the transparency alpha channel of the mask
         to clip the icon to a square with a 2-pixel border
         and rounded corners */

      /* Convert the mask pixbuf to a surface */
      cairo_surface_t *mask_surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, 64, 64);
      cairo_t *mask_cr = cairo_create (mask_surface);
      gdk_cairo_set_source_pixbuf (mask_cr, mask, 0, 0);
      cairo_paint (mask_cr);
      cairo_destroy (mask_cr);

      /* Draw the icon pattern, masked with the surface */
      cairo_mask_surface (cr, mask_surface, 0.0, 0.0);
      cairo_surface_destroy (mask_surface);
      g_object_unref (mask);
    }
  else
    {
      /* Not using a mask; just paint the icon pattern directly */
      cairo_paint (cr);
    }

  dest = gdk_pixbuf_get_from_surface (dest_surface, 0, 0, 64, 64);
  cairo_surface_destroy (dest_surface);
  cairo_pattern_destroy (icon_pattern);
  cairo_destroy (cr);

  return dest;
}

void
eos_save_icon (GdkPixbuf *pixbuf,
               const gchar *format,
               const gchar *filename)
{
  gdk_pixbuf_save (pixbuf, filename, format, NULL, NULL);
}

GdkNotifyType
eos_get_event_notify_type (GdkEvent *event)
{
  return ((GdkEventCrossing *) event)->detail;
}

char *
eos_get_updates_file (void)
{
  return g_build_filename (eos_get_cache_dir (), "updates.json", NULL);
}

char *
eos_get_all_updates_uri (void)
{
  return g_strconcat (eos_get_app_server_url (),
                      "/api/",
                      eos_get_app_server_api (),
                      "/updates/",
                      eos_get_os_version (),
                      "?arch=", get_os_arch (),
                      "&personality=", eos_get_os_personality (),
                      NULL);
}

char *
eos_get_updates_meta_record_file (void)
{
  return g_build_filename (eos_get_cache_dir (), "updates_meta.json", NULL);
}

char *
eos_get_updates_meta_record_uri (void)
{
  return g_strconcat (eos_get_app_server_url (),
                      "/api/v1/meta_records",
                      "?type=updates",
                      NULL);
}

static gboolean
is_app_id (const char *appid)
{
  static const char alsoallowed[] = "_-+.";
  static const char *reserveddirs[] = { "bin", "games", "share", "lost+found", "xdg", };

  if (!appid || appid[0] == '\0')
    return FALSE;

  guint i;
  for (i = 0; i < G_N_ELEMENTS (reserveddirs); i++)
    {
      if (g_strcmp0 (appid, reserveddirs[i]) == 0)
        return FALSE;
    }

  if (!g_ascii_isalnum (appid[0]))
    return FALSE; /* must start with an alphanumeric character */

  int c;
  while ((c = *appid++) != '\0')
    {
      if (!g_ascii_isalnum (c) && !strchr (alsoallowed, c))
        break;
    }

  if (!c)
    return TRUE;

  return FALSE;
}

gboolean
eos_app_load_installed_apps (GHashTable *app_info,
                             GCancellable *cancellable)
{
  const char *prefix = eos_get_bundles_dir ();
  GError *error = NULL;
  GDir *dir = g_dir_open (prefix, 0, &error);
  if (dir == NULL)
    {
      eos_app_log_error_message ("Unable to open '%s': %s", prefix, error->message);
      g_error_free (error);
      return FALSE;
    }

  gint64 start_time = g_get_monotonic_time ();

  int n_bundles = 0;
  const char *appid;
  while ((appid = g_dir_read_name (dir)) != NULL)
    {
      if (g_cancellable_is_cancelled (cancellable))
        break;

      if (!is_app_id (appid))
        {
          eos_app_log_info_message ("Skipping '%s/%s': not a valid app directory", prefix, appid);
          continue;
        }

      char *info_path = g_build_filename (prefix, appid, ".info", NULL);
      eos_app_log_info_message ("Loading bundle info for '%s' from '%s'...", appid, info_path);

      char *desktop_id = g_strconcat (appid, ".desktop", NULL);
      EosAppInfo *info = g_hash_table_lookup (app_info, desktop_id);

      if (info == NULL)
        {
          info = eos_app_info_new (appid);
          g_hash_table_insert (app_info, g_strdup (desktop_id), info);
        }

      if (eos_app_info_update_from_installed (info, info_path))
        n_bundles += 1;

      g_free (desktop_id);
      g_free (info_path);
    }

  g_dir_close (dir);

  eos_app_log_debug_message ("Bundle loading from '%s': %d bundles, %.3f msecs",
                             prefix,
                             n_bundles,
                             (double) (g_get_monotonic_time () - start_time) / 1000);

  return TRUE;
}

static gboolean
eos_app_get_monotonic_id_from_json (JsonObject *obj,
                                    gint64 *monotonic_id,
                                    GError **error)
{
  if (!json_object_has_member (obj, "monotonic_id"))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_MISSING_ATTRIBUTE,
                           _("Updates meta record did not contain "
                             "expected attributes"));

      eos_app_log_error_message ("Updates meta record did not contain "
                                 "expected attributes");

      return FALSE;
    }

  eos_app_log_debug_message ("Loading JSON update meta record monotonic id");

  if (json_object_get_null_member (obj, "monotonic_id"))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_VALUE,
                           _("Updates meta record did not contain "
                             "valid monotonic_id attribute value"));

      eos_app_log_error_message ("Updates meta record did not contain "
                                 "valid monotonic_id attribute value");

      return FALSE;
    }

  *monotonic_id = json_object_get_int_member (obj, "monotonic_id");

  eos_app_log_debug_message ("Update meta record monotonic id: %" G_GINT64_FORMAT,
                             *monotonic_id);

  return TRUE;
}

static gboolean
eos_app_get_string_member_from_json (JsonObject *obj,
                                     const char *member,
                                     char **member_text,
                                     GError **error)
{
  g_assert_nonnull (member_text);

  eos_app_log_debug_message ("Loading string member '%s' from updates "
                             "meta record", member);

  if (!json_object_has_member (obj, member))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_MISSING_ATTRIBUTE,
                           _("Updates meta record did not contain "
                             "expected string attributes"));

      eos_app_log_error_message ("Updates meta record did not contain "
                                 "expected string attribute '%s'", member);

      return FALSE;
    }

  *member_text = g_strdup (json_object_get_string_member (obj, member));

  eos_app_log_debug_message ("Update meta record %s: %s", member, *member_text);

  return TRUE;
}

gboolean
eos_app_load_updates_meta_record (gint64 *monotonic_update_id,
                                  char **os_version,
                                  char **os_personality,
                                  const char *data,
                                  GCancellable *cancellable,
                                  GError **error)
{
  eos_app_log_debug_message ("Parsing updates meta record");

  if (g_cancellable_is_cancelled (cancellable))
    {
      g_set_error_literal (error, G_IO_ERROR, G_IO_ERROR_CANCELLED,
                           _("Operation cancelled"));

      eos_app_log_error_message ("Operation cancelled");

      return FALSE;
    }

  JsonParser *parser = json_parser_new ();

  if (!json_parser_load_from_data (parser, data, -1, error))
    {
      eos_app_log_error_message ("Updates meta record wasn't able to be parsed");

      g_object_unref (parser);
      return FALSE;
    }

  JsonNode *root = json_parser_get_root (parser);
  if (!JSON_NODE_HOLDS_OBJECT (root))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_STRUCTURE,
                           _("Updates meta record did not contain "
                             "expected structure"));

      eos_app_log_error_message ("Updates meta record did not contain "
                                 "expected structure");

      g_object_unref (parser);
      return FALSE;
    }

  JsonObject *obj = json_node_get_object (root);
  gboolean ret = eos_app_get_monotonic_id_from_json (obj, monotonic_update_id,
                                                     error);

  if (ret && os_version)
    {
      ret = eos_app_get_string_member_from_json (obj, "os-version", os_version,
                                                 error);
    }

  if (ret && os_personality)
    {
      ret = eos_app_get_string_member_from_json (obj, "os-personality",
                                                 os_personality, error);
    }

  g_object_unref (parser);

  return ret;
}

gboolean
eos_app_set_os_details_in_updates_meta_record (GError **error_out)
{
  const char *record_file = eos_get_updates_meta_record_file ();
  g_autoptr (JsonParser) parser = json_parser_new ();
  g_autoptr (JsonGenerator) generator = NULL;
  g_autoptr (JsonNode) node = NULL;
  GError *error = NULL;
  JsonNode *root;
  JsonObject *obj;
  gboolean changed = FALSE;

  eos_app_log_info_message ("Setting OS version and personality in updates "
                            "meta record: %s", record_file);

  if (!json_parser_load_from_file (parser, record_file, &error))
    {
      eos_app_log_error_message ("Error loading json from meta record file: %s",
                                 error->message);
      g_propagate_error (error_out, error);

      return FALSE;
    }

  root = json_parser_get_root (parser);

  /* copying the root node as docs say it should never be modified */
  node = json_node_copy (root);
  obj = json_node_get_object (node);

  if (!json_object_has_member (obj, "os-version"))
    {
      json_object_set_string_member (obj, "os-version", eos_get_os_version ());
      changed = TRUE;
    }

  if (!json_object_has_member (obj, "os-personality"))
    {
      json_object_set_string_member (obj,
                                     "os-personality",
                                     eos_get_os_personality ());
      changed = TRUE;
    }

  if (!changed)
    {
      eos_app_log_debug_message ("Updates meta record already has OS version "
                                 "and personality. Nothing to be done.");

      return TRUE;
    }

  generator = json_generator_new ();
  json_generator_set_root (generator, node);

  eos_app_log_debug_message ("Saving OS version and personality in "
                             "updates meta record file.");

  return json_generator_to_file (generator, record_file, error_out);
}

static JsonObject *
get_matching_version_delta (GList *deltas,
                            const char *version,
                            const char *installed_version)
{
  eos_app_log_debug_message (" - Looking for matching delta version: %s -> %s",
                             installed_version,
                             version);

  /* Remove older (not relevant) deltas from temp array */
  for (GList *iterator = deltas; iterator; iterator = iterator->next)
    {
      JsonObject *obj = iterator->data;
      const char *code_version = json_object_get_string_member (obj, "codeVersion");
      const char *from_version = json_object_get_string_member (obj, "fromVersion");

      if (eos_compare_versions (code_version, version) == 0 &&
          eos_compare_versions (installed_version, from_version) == 0)
        {
          eos_app_log_debug_message (" - Found matching delta");
          return obj;
        }
    }

  return NULL;
}

static GList *
remove_records_version_lte (GList *deltas,
                            const char *version)
{
  eos_app_log_debug_message (" - Removing old/current/irrelevant deltas "
                             "from our temp list");

  GList *next = NULL;
  GList *new_list = deltas;
  for (GList *iterator = deltas; iterator; iterator = next)
    {
      JsonObject *obj = iterator->data;
      const char *code_version = json_object_get_string_member (obj, "codeVersion");
      const char *from_version = json_object_get_string_member (obj, "fromVersion");

      next = iterator->next;

      if (eos_compare_versions (code_version, version) <= 0)
        {
          eos_app_log_debug_message (" - Deleting delta %s -> %s", from_version,
                                     code_version);
          new_list = g_list_delete_link (new_list, iterator);
          json_object_unref (obj);
        }
    }

  return new_list;
}

static void
add_delta_to_temp_records (GHashTable *temp_delta_map,
                           const char *app_id,
                           JsonObject *obj)
{
  GList *deltas = g_hash_table_lookup (temp_delta_map, app_id);
  GList *new_delta_list = g_list_prepend (deltas, json_object_ref (obj));

  g_hash_table_steal (temp_delta_map, app_id);
  g_hash_table_insert (temp_delta_map, g_strdup (app_id), new_delta_list);
}

/* Functions to clear our newer_deltas hashtable */
static void
free_json_object_glist (gpointer data)
{
  g_list_free_full (data, (GDestroyNotify) json_object_unref);
}

static gboolean
is_server_record_valid (JsonNode *element)
{
  if (!JSON_NODE_HOLDS_OBJECT (element))
    {
      eos_app_log_error_message (" - JSON element contains unknown type of data! "
                                 "Ignoring!");
      return FALSE;
    }

  JsonObject *obj = json_node_get_object (element);
  if (!json_object_has_member (obj, "appId"))
    {
      eos_app_log_error_message (" - JSON element doesn't contain an appId! "
                                 "Ignoring!");
      return FALSE;
    }

  if (!json_object_has_member (obj, "codeVersion"))
    {
      eos_app_log_error_message (" - JSON element doesn't contain codeVersion attribute! "
                                 "Ignoring!");
      return FALSE;
    }

  if (!json_object_has_member (obj, "isDiff"))
    {
      eos_app_log_error_message (" - JSON element doesn't contain isDiff attribute! "
                                 "Ignoring!");
      return FALSE;
    }

  if (json_object_get_boolean_member (obj, "isDiff"))
    {
      if (json_object_get_string_member (obj, "fromVersion") == NULL)
        {
          eos_app_log_error_message (" - JSON element doesn't contain fromVersion "
                                     "attribute! Ignoring!");
          return FALSE;
        }
    }

  return TRUE;
}

gboolean
eos_app_load_available_apps (GHashTable *app_info,
                             GCancellable *cancellable,
                             GError **error)
{
  char *path;
  char *data = NULL;
  gboolean res = FALSE;

  path = eos_get_updates_file ();
  if (g_file_get_contents (path, &data, NULL, error))
    res = eos_app_load_available_apps_from_data (app_info, data,
                                                 cancellable, error);

  g_free (data);
  g_free (path);

  return res;
}

gboolean
eos_app_load_available_apps_from_data (GHashTable *app_info,
                                       const char *data,
                                       GCancellable *cancellable,
                                       GError **error)
{
  JsonParser *parser = json_parser_new ();
  gboolean retval = FALSE;
  gint64 start_time = g_get_monotonic_time ();
  GHashTable *newer_deltas = g_hash_table_new_full (g_str_hash, g_str_equal,
                                                    g_free,
                                                    free_json_object_glist);

  if (!json_parser_load_from_data (parser, data, -1, error))
    {
      eos_app_log_error_message ("Update records weren't able to be parsed");
      goto out;
    }

  JsonNode *root = json_parser_get_root (parser);
  if (!JSON_NODE_HOLDS_ARRAY (root))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_UNEXPECTED_STRUCTURE,
                           "Update records did not contain expected structure");

      eos_app_log_error_message ("Update records did not contain "
                                 "expected structure");
      goto out;
    }

  eos_app_log_debug_message ("Iterating over the update list");

  JsonArray *array = json_node_get_array (root);
  guint record_count = json_array_get_length (array);

  for (guint index = 0; index < record_count; index++)
    {
      if (g_cancellable_is_cancelled (cancellable))
        {
          g_set_error_literal (error, G_IO_ERROR,
                               G_IO_ERROR_CANCELLED,
                               "Operation was cancelled");
          eos_app_log_info_message (" - Reading of update list canceled");
          goto out;
        }

      JsonNode *element = json_array_get_element (array, index);
      if (!is_server_record_valid (element))
          continue;

      JsonObject *obj = json_node_get_object (element);

      const char *app_id = json_object_get_string_member (obj, "appId");
      const gboolean is_diff = json_object_get_boolean_member (obj, "isDiff");
      const char *code_version = json_object_get_string_member (obj, "codeVersion");

      if (is_diff && !eos_use_delta_updates ())
        {
          eos_app_log_debug_message ("Deltas disabled. Ignoring diff for %s", app_id);

          continue;
        }

      /* Grab fromVersion field for deltas */
      const char *from_version = NULL;
      if (is_diff)
          from_version = json_object_get_string_member (obj, "fromVersion");

      eos_app_log_debug_message ("Loading: '%s (diff: %s) %s -> %s'",
                                app_id,
                                is_diff ? "true" : "false",
                                from_version == NULL ? "None" : from_version,
                                code_version);

      const char *stored_code_version = NULL;
      char *desktop_id = g_strconcat (app_id, ".desktop", NULL);
      EosAppInfo *info = g_hash_table_lookup (app_info, desktop_id);

      if (info == NULL)
        {
          if (is_diff)
            {
              /* This logic saves any deltas into our temp structure until we
                 get a matching full update and doesn't change the app_info
                 so that we can install apps that have higher deltas. Sadly
                 this does prevent upgrades to a newer version with a delta if
                 there is no matching full update since at that point we would
                 need to retain different available versions (1 full, 1 delta)
                 but at this point, that situation should never occur. */
              eos_app_log_debug_message (" -> First time encountering app. "
                                         "Saving delta as possible upgrade path.");

              add_delta_to_temp_records (newer_deltas, app_id, obj);

              g_free (desktop_id);
              continue;
            }
          else
            {
              /* New record. Save but continue the logic since we may have
                 some deltas waiting to be assigned to the app_info */
              eos_app_log_debug_message (" -> First time encountering app. "
                                         "Creating new record.");

              info = eos_app_info_new (app_id);
              eos_app_info_update_from_server (info, obj);

              g_hash_table_insert (app_info, g_strdup (desktop_id), info);
            }
        }
      else
        {
          stored_code_version = eos_app_info_get_available_version (info);
        }

      g_free (desktop_id);

      /* Info shouldn't be ever null at this point */
      g_assert (info != NULL);

      const int version_cmp = eos_compare_versions (code_version, stored_code_version);
      eos_app_log_debug_message (" - Version comparison: [new: %s, have: %s, diff: %d].",
                                 code_version,
                                 stored_code_version,
                                 version_cmp);

      GList *deltas_for_app_id = g_hash_table_lookup (newer_deltas, app_id);

      /* TODO: Modularize, if possible */
      if (is_diff)
        {
          if (eos_compare_versions (from_version,
                                    eos_app_info_get_installed_version (info)) != 0)
            {
              eos_app_log_debug_message (" -> Delta from_version (%s) does not match "
                                         "installed version (%s). Ignoring.",
                                         from_version,
                                         eos_app_info_get_installed_version (info));

              continue;
            }

          if (eos_app_info_is_available (info)) /* We have a full update */
            {
              if (version_cmp > 0)
                {
                  eos_app_log_debug_message (" -> Preserving delta of version: %s (%d)",
                                             code_version,
                                             version_cmp);
                  add_delta_to_temp_records (newer_deltas, app_id, obj);
                }
              else if (version_cmp == 0)
                {
                  eos_app_log_debug_message (" -> Found matching delta for version: %s",
                                             stored_code_version);

                  eos_app_info_update_from_server (info, obj);
                }
              else
                {
                  eos_app_log_debug_message (" -> Delta (%s) is lower version than %s. "
                                             "Ignoring.",
                                             code_version,
                                             stored_code_version);
                }
            }
          else /* We only have the delta in info */
            {
              /* We save all deltas until we get a full update record since
                 we won't know what is a good delta version to keep */
              eos_app_log_debug_message (" -> Preserving delta of version: %s",
                                         code_version);
              add_delta_to_temp_records (newer_deltas, app_id, obj);
            }
        }
      else /* Full version */
        {
          if (version_cmp > 0)
            {
              eos_app_log_debug_message (" -> Full version newer than in our records. "
                                         "Updating record.");

              eos_app_info_clear_server_update_attributes (info);
              eos_app_info_update_from_server (info, obj);

              JsonObject *delta_object = get_matching_version_delta (deltas_for_app_id,
                                                                     code_version,
                                                                     eos_app_info_get_installed_version (info));

              if (delta_object)
                {
                  eos_app_log_debug_message (" -> Found matching delta for version: %s. "
                                             "Updating delta record.",
                                             code_version);

                  /* Update delta fields */
                  eos_app_info_update_from_server (info, delta_object);

                  /* Remove any older deltas that we held onto */
                  GList *new_delta_list = remove_records_version_lte (deltas_for_app_id,
                                                                      code_version);

                  g_hash_table_steal (newer_deltas, app_id);
                  g_hash_table_insert (newer_deltas, g_strdup (app_id), new_delta_list);
                }
              else
                {
                  eos_app_log_debug_message (" -> No matching delta for version: %s",
                                             code_version);
                }
            }
          else if (version_cmp == 0)
            {
              if (eos_compare_versions (code_version,
                                        eos_app_info_get_installed_version (info)) != 0)
                {
                   eos_app_log_debug_message (" -> Full bundle has an override. "
                                              "Ignoring");
                   continue;
                }

              eos_app_log_debug_message (" -> Full bundle matches installed version. "
                                         "Updating record");
              eos_app_info_update_from_server (info, obj);
            }
          else
            {
              eos_app_log_debug_message (" -> Full bundle is not a newer version. (%d)"
                                         "Skipping",
                                         version_cmp);
            }
        }
    }

  eos_app_log_info_message ("Processed %d records in %.0f ms",
                            record_count,
                            (double) (g_get_monotonic_time () - start_time) / 1000);

  retval = TRUE;

 out:
  g_hash_table_unref (newer_deltas);
  g_object_unref (parser);

  return retval;
}

static gchar *
app_id_from_gio_desktop_id (const gchar *desktop_id)
{
  gint len;
  const char *ptr = desktop_id;

  if (g_str_has_prefix (ptr, "eos-app-"))
    ptr += 8; /* the 8 here is the length of "eos-app-" */

  len = strlen (ptr);
  return g_strndup (ptr, len - 8); /* the 8 here is the length of ".desktop" */
}

static gboolean
app_is_visible (GAppInfo *info)
{
  GDesktopAppInfo *desktop_info = G_DESKTOP_APP_INFO (info);

  return !g_desktop_app_info_get_nodisplay (desktop_info) &&
    !g_desktop_app_info_get_is_hidden (desktop_info);
}

static GHashTable *
load_apps_from_gio (void)
{
  GList *all_infos, *l;
  GAppInfo *info;
  GHashTable *set;

  all_infos = g_app_info_get_all ();
  set = g_hash_table_new_full (g_str_hash, g_str_equal,
                               NULL,
                               g_object_unref);

  for (l = all_infos; l != NULL; l = l->next)
    {
      info = l->data;

      if (app_is_visible (info))
        g_hash_table_insert (set, (gpointer) g_app_info_get_id (info), info);
      else
        g_object_unref (info);
    }

  g_list_free (all_infos);
  return set;
}

void
eos_app_load_gio_apps (GHashTable *app_info)
{
  GList *l, *gio_apps;
  GHashTable *apps;
  GHashTableIter iter;
  const char *desktop_id;
  EosAppInfo *info;

  eos_app_log_debug_message ("Reloading GIO apps");
  apps = load_apps_from_gio ();
  gio_apps = g_hash_table_get_values (apps);

  for (l = gio_apps; l != NULL; l = l->next)
    {
      GDesktopAppInfo *desktop_info = l->data;

      desktop_id = g_app_info_get_id (G_APP_INFO (desktop_info));

      char *app_id = app_id_from_gio_desktop_id (desktop_id);
      char *sanitized_desktop_id = g_strconcat (app_id, ".desktop", NULL);

      info = g_hash_table_lookup (app_info, sanitized_desktop_id);

      if (info == NULL)
        {
          info = eos_app_info_new (app_id);
          g_hash_table_insert (app_info, g_strdup (sanitized_desktop_id), info);
        }

      g_free (app_id);
      g_free (sanitized_desktop_id);

      eos_app_info_update_from_gio (info, desktop_info);
    }

  g_list_free (gio_apps);

  g_hash_table_iter_init (&iter, app_info);
  while (g_hash_table_iter_next (&iter, (gpointer *) &desktop_id, (gpointer *) &info))
    eos_app_info_set_is_installed (info,
                                   g_hash_table_contains (apps, desktop_id));

  g_hash_table_unref (apps);
}

static GHashTable *
load_shell_apps_from_gvariant (GVariant *apps)
{
  GHashTable *retval;
  GVariantIter *iter;
  gchar *application;

  retval = g_hash_table_new_full (g_str_hash, g_str_equal,
                                  g_free, NULL);

  g_variant_get (apps, "(as)", &iter);

  while (g_variant_iter_loop (iter, "s", &application))
    g_hash_table_add (retval, g_strdup (application));

  g_variant_iter_free (iter);

  return retval;
}

void
eos_app_load_shell_apps (GHashTable *app_info,
                         GVariant *shell_apps)
{
  GHashTable *apps;
  GHashTableIter iter;
  char *desktop_id;
  EosAppInfo *info;

  apps = load_shell_apps_from_gvariant (shell_apps);

  g_hash_table_iter_init (&iter, app_info);
  while (g_hash_table_iter_next (&iter, (gpointer *) &desktop_id, (gpointer *) &info))
    eos_app_info_set_has_launcher (info,
                                   g_hash_table_contains (apps, desktop_id));

  g_hash_table_unref (apps);
}

/* Keep in the same order as the EosAppCategory enumeration */
static const struct {
  const EosAppCategory category;
  const char *id;
} categories[] = {
  /* Translators: use the same string used to install the app center content JSON */
  { EOS_APP_CATEGORY_EDUCATION,     N_("Education") },
  { EOS_APP_CATEGORY_GAMES,         N_("Games") },
  { EOS_APP_CATEGORY_RESOURCES,     N_("Resources") },
  { EOS_APP_CATEGORY_UTILITIES,     N_("Utilities") },
};

static const guint n_categories = G_N_ELEMENTS (categories);

EosAppCategory
eos_app_category_from_id (const char *p)
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

typedef struct {
  char *version;
  char *revision;
  guint epoch;
} PkgVersion;

static gboolean
pkg_version_init (PkgVersion *ver,
                  const char *str)
{
  const gchar *end, *ptr;

  ver->version = ver->revision = NULL;

  if (str == NULL || *str == '\0')
    return FALSE;

  if (!g_str_is_ascii (str))
    return FALSE;

  /* Trim leading and trailing space. */
  while (*str && g_ascii_isspace (*str))
    str++;

  /* String now points to the first non-whitespace char. */
  end = str;

  /* Find either the end of the string, or a whitespace char. */
  while (*end && !g_ascii_isspace (*end))
    end++;

  /* Check for extra chars after trailing space. */
  ptr = end;
  while (*ptr && g_ascii_isspace (*ptr))
    ptr++;

  if (*ptr)
    return FALSE; /* version string has embedded spaces */

  char *colon = strchr (str, ':');
  if (colon)
    {
      char *eepochcolon;
      double epoch = g_strtod (str, &eepochcolon);

      if (colon != eepochcolon)
        return FALSE; /* epoch is not a number */

      if (epoch < 0)
        return FALSE; /* epoch is negative */

      if (epoch > G_MAXINT)
        return FALSE; /* epoch is too big */

      if (!*++colon)
        return FALSE; /* nothing after colon in version number */

      str = colon;

      ver->epoch = epoch;
    }
  else
    ver->epoch = 0;

  ver->version = g_strndup (str, end - str);

  char *hyphen = strrchr (ver->version, '-');
  if (hyphen)
    *hyphen++ = '\0';

  ver->revision = hyphen ? g_strdup (hyphen) : NULL;

  ptr = ver->version;
  if (ptr != NULL && *ptr && !g_ascii_isdigit (*ptr++))
    return FALSE; /* version number doesn't start with digit */

  for (; ptr && *ptr; ptr++)
    {
      if (!g_ascii_isdigit (*ptr) &&
          !g_ascii_isalpha (*ptr) &&
          strchr (".-+~:", *ptr) == NULL)
        return FALSE; /* invalid character in version number */
    }

  for (ptr = ver->revision; ptr && *ptr; ptr++)
    {
      if (!g_ascii_isdigit (*ptr) &&
          !g_ascii_isalpha (*ptr) &&
          strchr (".+~", *ptr) == NULL)
        return FALSE; /* invalid characters in revision number */
    }

  return TRUE;
}

static void
pkg_version_clear (PkgVersion *ver)
{
  g_free (ver->version);
  g_free (ver->revision);
}

static gint
order (gint c)
{
  if (g_ascii_isdigit (c))
    return 0;

  if (g_ascii_isalpha (c))
    return c;

  if (c == '~')
    return -1;

  if (c)
    return c + 256;

  return 0;
}

static gint
verrevcmp (const char *a,
           const char *b)
{
  if (a == NULL)
    a = "";
  if (b == NULL)
    b = "";

  while (*a || *b) {
    int first_diff = 0;

    while ((*a && !g_ascii_isdigit (*a)) || (*b && !g_ascii_isdigit (*b))) {
      int ac = order (*a);
      int bc = order (*b);

      if (ac != bc)
        return ac - bc;

      a++;
      b++;
    }

    while (*a == '0')
      a++;

    while (*b == '0')
      b++;

    while (g_ascii_isdigit (*a) && g_ascii_isdigit (*b)) {
      if (!first_diff)
        first_diff = *a - *b;
      a++;
      b++;
    }

    if (g_ascii_isdigit (*a))
      return 1;
    if (g_ascii_isdigit (*b))
      return -1;
    if (first_diff)
      return first_diff;
  }

  return 0;
}

static int
pkg_version_compare (const PkgVersion *a,
                     const PkgVersion *b)
{
  int rc;

  if (a->epoch > b->epoch)
    return 1;

  if (a->epoch < b->epoch)
    return -1;

  rc = verrevcmp (a->version, b->version);
  if (rc)
    return rc;

  return verrevcmp (a->revision, b->revision);
}

int
eos_compare_versions (const char *a,
                      const char *b)
{
  PkgVersion ver_a, ver_b;

  /* Really quick shortcut */
  if (g_strcmp0 (a, b) == 0)
    return 0;

  /* Version A not valid or missing, so it's older */
  if (!pkg_version_init (&ver_a, a))
    return -1;

  /* Version B not valid or missing, so it's older */
  if (!pkg_version_init (&ver_b, b))
    return 1;

  int res = pkg_version_compare (&ver_a, &ver_b);

  pkg_version_clear (&ver_a);
  pkg_version_clear (&ver_b);

  return res;
}

gboolean
eos_check_available_space (GFile         *path,
                           goffset        min_size,
                           GCancellable  *cancellable,
                           GError       **error)
{
  g_return_val_if_fail (G_IS_FILE (path), FALSE);

  GFileInfo *info;
  gboolean retval = TRUE;

  info = g_file_query_filesystem_info (path,
                                       G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                       cancellable,
                                       error);

  if (info == NULL)
    {
      eos_app_log_error_message ("Can't get filesystem info to calculate "
                                 "the available space");
      return FALSE;
    }

  guint64 free_space = g_file_info_get_attribute_uint64 (info, G_FILE_ATTRIBUTE_FILESYSTEM_FREE);

  eos_app_log_info_message ("Space required: %lld KB",
                            (long long) (min_size / 1024));
  eos_app_log_info_message ("Space left on FS: %lld KB",
                            (long long) (min_size / 1024));

  if (free_space < min_size)
    {
      eos_app_log_error_message ("Not enough space on device for downloading app");

      g_set_error (error, EOS_APP_STORE_ERROR,
                   EOS_APP_STORE_ERROR_DISK_FULL,
                   _("Not enough space on device for downloading the app."));
      retval = FALSE;
    }

  g_object_unref (info);

  return retval;
}

gboolean
eos_mkdir_for_artifact (const char *target_file,
                        GError    **error)
{
  GFile *file = g_file_new_for_path (target_file);
  GFile *parent = g_file_get_parent (file);

  char *parent_path = NULL;

  gboolean retval = FALSE;

  parent_path = g_file_get_path (parent);
  if (g_mkdir_with_parents (parent_path, 0755) == -1)
    {
      int saved_errno = errno;

      g_set_error (error, G_IO_ERROR,
                   g_io_error_from_errno (saved_errno),
                   "Unable to create directory: %s",
                   g_strerror (saved_errno));

      goto out;
    }

  retval = TRUE;

out:
  g_free (parent_path);

  g_object_unref (parent);
  g_object_unref (file);

  return retval;
}

char *
eos_storage_type_to_string (EosStorageType storage)
{
  GEnumClass *enum_class = g_type_class_ref (EOS_TYPE_STORAGE_TYPE);
  GEnumValue *enum_value = g_enum_get_value (enum_class, storage);

  g_assert (enum_value != NULL);

  char *retval = g_strdup (enum_value->value_nick);
  g_type_class_unref (enum_class);

  return retval;
}

static void
on_eam_proxy_name_owner_changed (GDBusProxy *proxy,
                                 GParamSpec *pspec,
                                 gpointer user_data)
{
  EosAppManager **proxy_ptr = user_data;
  char *name_owner = g_dbus_proxy_get_name_owner (proxy);

  /* Whenever eam goes away, we invalidate our static proxy,
   * otherwise calls that would read cached properties will all
   * return NULL.
   */
  if (name_owner == NULL)
    g_clear_object (proxy_ptr);

  g_free (name_owner);
}

/**
 * eos_get_eam_dbus_proxy: (skip)
 */
EosAppManager *
eos_get_eam_dbus_proxy (void)
{
  static EosAppManager *proxy = NULL;

  eos_app_log_debug_message ("Getting dbus proxy");

  /* If we already have a proxy, return it */
  if (proxy != NULL)
    return proxy;

  /* Otherwise create it */
  GError *error = NULL;

  eos_app_log_debug_message ("No dbus proxy object yet - creating it");

  proxy = eos_app_manager_proxy_new_for_bus_sync (G_BUS_TYPE_SYSTEM,
                                                  G_DBUS_PROXY_FLAGS_NONE,
                                                  "com.endlessm.AppManager",
                                                  "/com/endlessm/AppManager",
                                                  NULL, /* GCancellable* */
                                                  &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to create dbus proxy: %s", error->message);
      g_error_free (error);
      return NULL;
    }

  g_dbus_proxy_set_default_timeout (G_DBUS_PROXY (proxy), G_MAXINT);
  g_signal_connect (proxy, "notify::g-name-owner",
                    G_CALLBACK (on_eam_proxy_name_owner_changed), &proxy);

  return proxy;
}

#define BLOCKSIZE 32768

G_DEFINE_AUTOPTR_CLEANUP_FUNC (FILE, fclose)

static gboolean
verify_checksum_hash (const char    *source_file,
                      const char    *checksum_str,
                      GChecksumType  checksum_type)
{
  gssize checksum_len = strlen (checksum_str);
  gssize hash_len = g_checksum_type_get_length (checksum_type) * 2;
  if (checksum_len < hash_len)
    return FALSE;

  g_autoptr(FILE) fp = fopen (source_file, "r");
  if (fp == NULL)
    return FALSE;

  g_autoptr(GChecksum) checksum = g_checksum_new (checksum_type);

  guint8 buffer[BLOCKSIZE];
  while (1) {
    size_t n = fread (buffer, 1, BLOCKSIZE, fp);
    if (n > 0) {
      g_checksum_update (checksum, buffer, n);
      continue;
    }

    if (feof (fp))
      break;

    if (ferror (fp))
      return FALSE;
  }

  const char *hash = g_checksum_get_string (checksum);

  return (g_ascii_strncasecmp (checksum_str, hash, hash_len) == 0);
}

gboolean
eos_app_utils_verify_checksum (const char *bundle_file,
                               const char *checksum_str,
                               GError **error)
{
  gboolean res = verify_checksum_hash (bundle_file, checksum_str, G_CHECKSUM_SHA256);

  if (!res)
    g_set_error_literal (error, EOS_APP_STORE_ERROR,
                         EOS_APP_STORE_ERROR_CHECKSUM_MISSING,
                         _("There was a problem downloading the app; "
                           "please try again"));

  return res;
}
