/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"

#include "eos-app-log.h"
#include "eos-link-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <json-glib/json-glib.h>
#include <errno.h>

#define APP_STORE_CONTENT_DIR   "application-store"
#define APP_STORE_CONTENT_APPS  "apps"
#define APP_STORE_CONTENT_LINKS "links"

#define BUNDLE_DIR              LOCALSTATEDIR "/tmp"
#define BUNDLE_DIR_TEMPLATE     LOCALSTATEDIR "/tmp/eos-app-store.XXXXXX"
#define APP_DIR_DEFAULT         "/endless"

G_DEFINE_QUARK (eos-app-utils-error-quark, eos_app_utils_error)

const char *
eos_get_bundle_download_dir (void)
{
  static char *bundle_dir;

  if (g_once_init_enter (&bundle_dir))
    {
      g_mkdir_with_parents (BUNDLE_DIR, 0755);

      char *tmp = g_strdup (BUNDLE_DIR_TEMPLATE);
      while (g_mkdtemp_full (tmp, 0755) == NULL)
        {
          int saved_errno = errno;

          eos_app_log_error_message ("Unable to create temporary directory: %s",
                                     g_strerror (saved_errno));
        }

      eos_app_log_info_message ("Bundle dir: %s", tmp);

      g_once_init_leave (&bundle_dir, tmp);
    }

  return bundle_dir;
}

void
eos_clear_bundle_download_dir (void)
{
  GFile *dir = g_file_new_for_path (eos_get_bundle_download_dir ());

  GError *error = NULL;
  GFileEnumerator *enumerator = g_file_enumerate_children (dir, G_FILE_ATTRIBUTE_STANDARD_NAME,
                                                           G_FILE_QUERY_INFO_NOFOLLOW_SYMLINKS,
                                                           NULL,
                                                           &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to enumerate bundle dir '%s': %s",
                                 eos_get_bundle_download_dir (),
                                 error->message);
      g_error_free (error);
      g_object_unref (dir);
      return;
    }

  GFileInfo *child_info = NULL;
  while ((child_info = g_file_enumerator_next_file (enumerator, NULL, &error)) != NULL)
    {
      GFile *child = g_file_get_child (dir, g_file_info_get_name (child_info));

      g_file_delete (child, NULL, &error);
      if (error != NULL)
        {
          eos_app_log_error_message ("Unable to delete file: %s", error->message);
          g_clear_error (&error);
        }

      g_clear_object (&child_info);
      g_object_unref (child);
    }

  if (error != NULL)
    {
      eos_app_log_error_message ("Enumeration failed: %s", error->message);
      g_clear_error (&error);
    }

  g_object_unref (enumerator);

  g_file_delete (dir, NULL, &error);
  if (error != NULL)
    {
      eos_app_log_error_message ("Unable to delete download dir: %s", error->message);
      g_clear_error (&error);
    }

  g_object_unref (dir);
}

static const char *
get_os_personality (void)
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
  static char *apps_dir;

  if (g_once_init_enter (&apps_dir))
    {
      char *tmp;

      GKeyFile *keyfile = g_key_file_new ();
      char *path = g_build_filename (SYSCONFDIR, "eos-app-manager", "eam-default.cfg", NULL);
      GError *error = NULL;
      g_key_file_load_from_file (keyfile, path, G_KEY_FILE_NONE, &error);
      if (error == NULL)
        tmp = g_key_file_get_string (keyfile, "eam", "appdir", &error);

      if (error != NULL)
        {
          eos_app_log_error_message ("Unable to load configuration: %s",
                                     error->message);
          g_error_free (error);
          tmp = g_strdup (APP_DIR_DEFAULT);
        }

      eos_app_log_info_message ("Bundles dir: %s", tmp);

      g_free (path);
      g_key_file_free (keyfile);

      g_once_init_leave (&apps_dir, tmp);
    }

  return apps_dir;
}

gboolean
eos_use_delta_updates (void)
{
  static char *deltaupdates;

  if (g_once_init_enter (&deltaupdates))
    {
      gboolean val = FALSE;
      char *tmp;

      GKeyFile *keyfile = g_key_file_new ();
      char *path = g_build_filename (SYSCONFDIR, "eos-app-manager", "eam-default.cfg", NULL);
      GError *error = NULL;
      g_key_file_load_from_file (keyfile, path, G_KEY_FILE_NONE, &error);
      if (error == NULL)
        val = g_key_file_get_boolean (keyfile, "eam", "deltaupdates", &error);

      if (error != NULL)
        {
          eos_app_log_error_message ("Unable to load configuration: %s",
                                     error->message);
          g_error_free (error);
        }

      eos_app_log_info_message ("Use delta updates: %s", val ? "yes" : "no");

      /* Need this trick because g_once_init_leave() does not accept 0 */
      tmp = val ? g_strdup ("true") : g_strdup ("false");

      g_free (path);
      g_key_file_free (keyfile);

      g_once_init_leave (&deltaupdates, tmp);
    }

  return g_strcmp0 (deltaupdates, "true") == 0;
}

const char *
eos_get_app_server_url (void)
{
  static char *server_url;

  if (g_once_init_enter (&server_url))
    {
      char *tmp;

      GKeyFile *keyfile = g_key_file_new ();
      char *path = g_build_filename (SYSCONFDIR, "eos-app-manager", "eam-default.cfg", NULL);
      GError *error = NULL;
      g_key_file_load_from_file (keyfile, path, G_KEY_FILE_NONE, &error);
      if (error == NULL)
        tmp = g_key_file_get_string (keyfile, "eam", "serveraddress", &error);

      if (error != NULL)
        {
          eos_app_log_error_message ("Unable to load configuration: %s",
                                     error->message);
          g_error_free (error);
          tmp = g_strdup ("http://appupdates.endlessm.com/");
        }

      eos_app_log_info_message ("Server address: %s", tmp);

      g_once_init_leave (&server_url, tmp);
    }

  return server_url;
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

static const char *
get_os_version (void)
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

static char *
eos_get_content_dir (const gchar *content_type)
{
  char *res = g_build_filename (DATADIR,
                                APP_STORE_CONTENT_DIR,
                                get_os_personality (),
                                content_type,
                                NULL);

  if (!g_file_test (res, G_FILE_TEST_EXISTS | G_FILE_TEST_IS_DIR))
    {
      g_free (res);

      res = g_build_filename (DATADIR,
                              APP_STORE_CONTENT_DIR,
                              "Default",
                              content_type,
                              NULL);
    }

  return res;
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
      g_critical ("Unable to load content from '%s': %s", content_file, error->message);
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
  if (!JSON_NODE_HOLDS_ARRAY (node))
    {
      g_set_error (error_out,
                   JSON_READER_ERROR,
                   JSON_READER_ERROR_NO_ARRAY,
                   "Expected array content");
      goto out_error;
    }

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
 * eos_app_get_content_dir:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_app_get_content_dir (void)
{
  return eos_get_content_dir (APP_STORE_CONTENT_APPS);
}

/**
 * eos_link_get_content_dir:
 *
 * ...
 *
 * Returns: (transfer full): ...
 */
char *
eos_link_get_content_dir (void)
{
  return eos_get_content_dir (APP_STORE_CONTENT_LINKS);
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

  JsonArray *categories_array = eos_app_parse_resource_content (APP_STORE_CONTENT_LINKS, get_os_personality (), NULL);

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
  json_array_unref (categories_array);

  return g_list_reverse (links);
}

void
eos_app_load_screenshot (GtkWidget  *image,
                         const char *path,
                         int         width)
{
  GError *error = NULL;
  GdkPixbuf *pixbuf =
    gdk_pixbuf_new_from_file_at_size (path, width, width, &error);

  if (error != NULL)
    {
      g_warning ("Cannot load image at path '%s': %s", path, error->message);
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
                      "/api/v1/updates/",
                      get_os_version (),
                      "?arch=", get_os_arch (),
                      "&personality=", get_os_personality (),
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
  static const char *reserveddirs[] = { "bin", "share", "lost+found", "xdg", };

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
                             GCancellable *cancellable,
                             GError **error)
{
  const char *appdir = eos_get_bundles_dir ();
  eos_app_log_info_message ("Reloading installed apps");

  GError *internal_error = NULL;
  GDir *dir = g_dir_open (appdir, 0, &internal_error);
  if (dir == NULL)
    {
      eos_app_log_error_message ("Unable to open '%s': %s", appdir, internal_error->message);
      g_propagate_error (error, internal_error);
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
          eos_app_log_info_message ("Skipping '%s/%s': not a valid app directory", appdir, appid);
          continue;
        }

      char *info_path = g_build_filename (appdir, appid, ".info", NULL);
      eos_app_log_info_message ("Loading bundle info for '%s' from '%s'...", appid, info_path);

      char *desktop_id = g_strconcat (appid, ".desktop", NULL);
      EosAppInfo *info = g_hash_table_lookup (app_info, desktop_id);
      g_free (desktop_id);

      if (info == NULL)
        info = eos_app_info_new (appid);
      else
        g_object_ref (info);

      if (eos_app_info_update_from_installed (info, info_path))
        {
          g_hash_table_replace (app_info,
                                g_strdup (eos_app_info_get_desktop_id (info)),
                                info);
          n_bundles += 1;
        }
      else
        {
          eos_app_log_error_message ("App '%s' failed to update from installed info", appid);
          g_object_unref (info);
        }

      g_free (info_path);
    }

  g_dir_close (dir);

  eos_app_log_debug_message ("Bundle loading: %d bundles, %.3f msecs",
                             n_bundles,
                             (double) (g_get_monotonic_time () - start_time) / 1000);

  return TRUE;
}

gboolean
eos_app_load_updates_meta_record (gint64 *monotonic_update_id,
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
  if (!json_object_has_member (obj, "monotonic_id"))
    {
      g_set_error_literal (error, EOS_APP_UTILS_ERROR,
                           EOS_APP_UTILS_ERROR_JSON_MISSING_ATTRIBUTE,
                           _("Updates meta record did not contain "
                             "expected attributes"));

      eos_app_log_error_message ("Updates meta record did not contain "
                                 "expected attributes");

      g_object_unref (parser);
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

      g_object_unref (parser);
      return FALSE;
    }

  *monotonic_update_id = json_object_get_int_member (obj, "monotonic_id");

  eos_app_log_debug_message ("Update meta record monotonic id: %" G_GINT64_FORMAT,
                             *monotonic_update_id);

  g_object_unref (parser);

  return TRUE;
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
          new_list = g_list_delete_link (deltas, iterator);
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

gboolean
eos_app_load_available_apps (GHashTable *app_info,
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

  guint array_length = json_array_get_length (array);

  /* TODO: Calculate this correctly */
  int n_available = array_length;

  for (guint index = 0; index < array_length; index++)
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
      if (!JSON_NODE_HOLDS_OBJECT (element))
        {
          eos_app_log_error_message (" - JSON element contains unknown type of data! "
                                     "Ignoring!");
          continue;
        }

      JsonObject *obj = json_node_get_object (element);
      if (!json_object_has_member (obj, "appId"))
        {
          eos_app_log_error_message (" - JSON element doesn't contain an appId! "
                                     "Ignoring!");
          continue;
        }

      if (!json_object_has_member (obj, "isDiff"))
        {
          eos_app_log_error_message (" - JSON element doesn't contain isDiff attribute! "
                                     "Ignoring!");
          continue;
        }

      if (!json_object_has_member (obj, "codeVersion"))
        {
          eos_app_log_error_message (" - JSON element doesn't contain codeVersion attribute! "
                                     "Ignoring!");
          continue;
        }

      const char *app_id = json_object_get_string_member (obj, "appId");
      const gboolean is_diff = json_object_get_boolean_member (obj, "isDiff");
      const char *code_version = json_object_get_string_member (obj, "codeVersion");

      /* Short-circuit if it's a diff and they're disabled */
      if (is_diff && !eos_use_delta_updates())
        {
          eos_app_log_debug_message ("Deltas disabled. Ignoring '%s (diff: %s)'",
                                     app_id,
                                     is_diff ? "true" : "false");

          continue;
        }

      /* Grab fromVersion field for deltas */
      const char *from_version = NULL;
      if (is_diff)
        {
          from_version = json_object_get_string_member (obj, "fromVersion");
          if (from_version == NULL)
            {
              eos_app_log_error_message (" - JSON element doesn't contain fromVersion "
                                         "attribute! Ignoring!");
              continue;
            }
        }

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

      /* If we have no availability version, just use the installed version */
      if (stored_code_version == NULL || *stored_code_version == '\0')
        stored_code_version = eos_app_info_get_installed_version (info);

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
                   eos_app_log_error_message (" -> Full bundle has an override. "
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

  retval = TRUE;
  eos_app_log_info_message ("Available bundles: %d bundles, %.3f msecs",
                            n_available,
                            (double) (g_get_monotonic_time () - start_time) / 1000);

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
          g_hash_table_replace (app_info, g_strdup (sanitized_desktop_id), info);
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
  /* Translators: use the same string used to install the app store content JSON */
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
eos_check_available_space (GFile         *file,
                           goffset        min_size,
                           GCancellable  *cancellable,
                           GError       **error)
{
  GFileInfo *info;
  gboolean retval = TRUE;

  if (file == NULL)
    eos_app_log_error_message ("File doesn't exist");

  eos_app_log_info_message ("Trying to get filesystem info from %s",
                            g_file_get_path(file));

  info = g_file_query_filesystem_info (file, G_FILE_ATTRIBUTE_FILESYSTEM_FREE,
                                       cancellable,
                                       error);
  if (info == NULL)
    {
      eos_app_log_error_message ("Can't get filesystem info to calculate"
                                 "the available space");
      return FALSE;
    }

  guint64 free_space = g_file_info_get_attribute_uint64 (info, G_FILE_ATTRIBUTE_FILESYSTEM_FREE);

  /* we try to be conservative, and reserve twice the requested size, like
   * eos-app-manager does.
   */
  guint64 req_space = min_size * 2;

  eos_app_log_info_message ("Space left on FS: %lldKB", (long long) (req_space/1024));

  if (free_space < req_space)
    {
      eos_app_log_error_message ("Not enough space on device for downloading app");

      g_set_error (error, EOS_APP_UTILS_ERROR,
                   EOS_APP_UTILS_ERROR_DISK_FULL,
                   _("Not enough space on device for downloading app"));
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
  gboolean res = TRUE;

  char *parent_path = g_file_get_path (parent);
  if (g_mkdir_with_parents (parent_path, 0755) == -1)
    {
      int saved_errno = errno;

      g_set_error (error, EOS_APP_UTILS_ERROR,
                   EOS_APP_UTILS_ERROR_FAILED_TO_CREATE_DIR,
                   "Unable to create directory: %s",
                   g_strerror (saved_errno));
      res = FALSE;
    }

  g_free (parent_path);

  g_object_unref (parent);
  g_object_unref (file);

  return res;
}
