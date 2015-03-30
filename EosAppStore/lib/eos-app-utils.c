/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*- */

#include "config.h"

#include "eos-app-utils.h"

#include "eos-app-log.h"
#include "eos-link-info.h"

#include <locale.h>
#include <glib/gi18n.h>
#include <json-glib/json-glib.h>

#define APP_STORE_CONTENT_DIR   "application-store"
#define APP_STORE_CONTENT_APPS  "apps"
#define APP_STORE_CONTENT_LINKS "links"

#define DOWNLOAD_DIR_DEFAULT    LOCALSTATEDIR "/tmp/eos-app-store"
#define APP_DIR_DEFAULT         "/endless"

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
eos_get_download_dir (void)
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

      g_once_init_leave (&apps_dir, tmp);
    }

  return apps_dir;
}

static const char *
get_app_server_url (void)
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

static JsonArray *
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
 * eos_app_load_content:
 * @category: ...
 * @callback: (allow-none) (scope call) (closure data): ...
 * @data: (allow-none): ...
 *
 * ...
 *
 * Return value: (transfer full) (element-type EosAppInfo): ...
 */
GList *
eos_app_load_content (EosAppCategory category,
                      EosAppFilterCallback callback,
                      gpointer data)
{
  JsonArray *array = eos_app_parse_resource_content (APP_STORE_CONTENT_APPS, "content", NULL);

  if (array == NULL)
    return NULL;

  GList *infos = NULL;

  guint i, n_elements = json_array_get_length (array);
  for (i = 0; i < n_elements; i++)
    {
      JsonNode *element = json_array_get_element (array, i);

      EosAppInfo *info = eos_app_info_create_from_content (element);
      if (info == NULL)
        continue;

      if (category == EOS_APP_CATEGORY_INSTALLED ||
          category == EOS_APP_CATEGORY_ALL)
        {
          /* do nothing */
        }
      else
        {
          if (category != eos_app_info_get_category (info))
            {
              eos_app_info_unref (info);
              continue;
            }

        }

      if (callback != NULL)
        {
          gboolean res;

          res = callback (info, data);
          if (!res)
            {
              eos_app_info_unref (info);
              continue;
            }
        }

      infos = g_list_prepend (infos, info);
    }

  json_array_unref (array);

  return g_list_reverse (infos);
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
      g_critical ("Unable to find category '%s'", category_name);
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
  return g_build_filename (eos_get_download_dir (), "updates.json", NULL);
}

char *
eos_get_all_updates_uri (void)
{
  return g_strconcat (get_app_server_url (),
                      "/api/v1/updates/",
                      get_os_version (),
                      "?arch=", get_os_arch (),
                      "&personality=", get_os_personality (),
                      NULL);
}

static gboolean
is_app_id (const char *appid)
{
  static const char alsoallowed[] = "-+.";
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
                             const char *appdir,
                             GCancellable *cancellable,
                             GError **error)
{
  GDir *dir = g_dir_open (appdir, 0, error);
  if (dir == NULL)
    return FALSE;

  gint64 start_time = g_get_monotonic_time ();

  int n_bundles = 0;
  const char *appid;
  while ((appid = g_dir_read_name (dir)) != NULL)
    {
      if (g_cancellable_is_cancelled (cancellable))
        break;

      if (!is_app_id (appid))
        {
          eos_app_log_info_message ("Skipping '%s'...", appid);
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
        eos_app_info_ref (info);

      if (eos_app_info_update_from_installed (info, info_path))
        {
          g_hash_table_replace (app_info,
                                g_strdup (eos_app_info_get_desktop_id (info)),
                                info);
          n_bundles += 1;
        }
      else
        {
          eos_app_log_debug_message ("App '%s' failed to update from installed info", appid);
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
eos_app_load_available_apps (GHashTable *app_info,
                             const char *data,
                             GCancellable *cancellable,
                             GError **error)
{
  JsonParser *parser = json_parser_new ();

  gint64 start_time = g_get_monotonic_time ();

  if (!json_parser_load_from_data (parser, data, -1, error))
    {
      g_object_unref (parser);
      return FALSE;
    }

  JsonNode *root = json_parser_get_root (parser);
  if (!JSON_NODE_HOLDS_ARRAY (root))
    {
      g_object_unref (parser);
      return FALSE;
    }

  int n_available = 0;
  JsonArray *array = json_node_get_array (root);
  guint i, len = json_array_get_length (array);
  for (i = 0; i < len; i++)
    {
      JsonNode *element;

      if (g_cancellable_is_cancelled (cancellable))
        break;

      element = json_array_get_element (array, i);

      if (!JSON_NODE_HOLDS_OBJECT (element))
        continue;

      JsonObject *obj = json_node_get_object (element);
      if (!json_object_has_member (obj, "appId"))
        continue;

      const char *appid = json_object_get_string_member (obj, "appId");
      eos_app_log_info_message ("Loading JSON server info for '%s'", appid);

      char *desktop_id = g_strconcat (appid, ".desktop", NULL);
      EosAppInfo *info = g_hash_table_lookup (app_info, desktop_id);
      g_free (desktop_id);

      if (info == NULL)
        info = eos_app_info_new (appid);
      else
        eos_app_info_ref (info);

      if (eos_app_info_update_from_server (info, element))
        {
          g_hash_table_replace (app_info,
                                g_strdup (eos_app_info_get_desktop_id (info)),
                                info);
          n_available += 1;
        }
      else
        eos_app_log_debug_message ("App '%s' does not have updates", appid);
    }

  g_object_unref (parser);

  eos_app_log_debug_message ("Available bundles: %d bundles, %.3f msecs",
                             n_available,
                             (double) (g_get_monotonic_time () - start_time) / 1000);

  return TRUE;
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
