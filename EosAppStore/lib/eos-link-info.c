#include "config.h"

#include "eos-link-info.h"
#include "eos-app-utils.h"

struct _EosLinkInfo
{
  volatile int ref_count;

  gchar *id;
  gchar *title;
  gchar *description;
  gchar *icon_filename;
  gchar *thumbnail_filename;
  GdkPixbuf *icon;
  GdkPixbuf *thumbnail;
  gchar *url;
};

G_DEFINE_BOXED_TYPE (EosLinkInfo, eos_link_info, eos_link_info_ref, eos_link_info_unref)

EosLinkInfo *
eos_link_info_new (void)
{
  EosLinkInfo *info = g_slice_new (EosLinkInfo);

  info->ref_count = 1;

  return info;
}

EosLinkInfo *
eos_link_info_ref (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  g_atomic_int_inc (&(info->ref_count));

  return info;
}

void
eos_link_info_unref (EosLinkInfo *info)
{
  g_return_if_fail (info != NULL);

  if (g_atomic_int_dec_and_test (&(info->ref_count)))
    {
      g_free (info->id);
      g_free (info->title);
      g_free (info->description);
      g_free (info->icon_filename);
      g_free (info->thumbnail_filename);
      g_clear_object (&(info->icon));
      g_clear_object (&(info->thumbnail));
      g_free (info->url);

      g_slice_free (EosLinkInfo, info);
    }
}

const gchar *
eos_link_info_get_id (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->id;
}

const gchar *
eos_link_info_get_title (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->title;
}

const gchar *
eos_link_info_get_description (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->description;
}

const gchar *
eos_link_info_get_icon_filename (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->icon_filename;
}

const gchar *
eos_link_info_get_thumbnail_filename (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->thumbnail_filename;
}

/**
 * eos_link_info_get_icon:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer none): ...
 */
GdkPixbuf *
eos_link_info_get_icon (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->icon;
}

/**
 * eos_link_info_get_thumbnail:
 * @info: ...
 *
 * ...
 *
 * Returns: (transfer none): ...
 */
GdkPixbuf *
eos_link_info_get_thumbnail (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, NULL);

  return info->thumbnail;
}

const gchar *
eos_link_info_get_url (EosLinkInfo *info)
{
  g_return_val_if_fail (info != NULL, "");

  return info->url;
}

/*< private >*/
EosLinkInfo *
eos_link_info_create_from_json (JsonNode *node)
{
  EosLinkInfo *info;
  JsonObject *obj;
  gchar *path;
  gchar *thumbnail_filename;
  gchar *icon_filename;

  g_return_val_if_fail (JSON_NODE_HOLDS_OBJECT (node), NULL);

  obj = json_node_get_object (node);
  info = eos_link_info_new ();

  if (json_object_has_member (obj, "linkId"))
    info->id = json_node_dup_string (json_object_get_member (obj, "linkId"));
  else
    info->id = NULL;

  if (json_object_has_member (obj, "linkName"))
    info->title = json_node_dup_string (json_object_get_member (obj, "linkName"));
  else
    info->title = g_strdup ("");

  if (json_object_has_member (obj, "linkSubtitle"))
    info->description = json_node_dup_string (json_object_get_member (obj, "linkSubtitle"));
  else
    info->description = g_strdup ("");
  
  if (json_object_has_member (obj, "linkIcon")) {
    path = eos_link_get_content_dir();
    icon_filename = g_build_filename (path,
				      json_node_get_string (json_object_get_member (obj, "linkIcon")),
				      NULL);
    info->icon = gdk_pixbuf_new_from_file (icon_filename, NULL);
    g_free (path);
    if (info->icon)
      info->icon_filename = icon_filename;
    else {
      info->icon_filename = NULL;
      g_free (icon_filename);
    }
  } else {
    info->icon = NULL;
    info->icon_filename = NULL;
  }

  if (json_object_has_member (obj, "linkSmall")) {
    path = eos_link_get_content_dir();
    thumbnail_filename = g_build_filename (path,
					   json_node_get_string (json_object_get_member (obj, "linkSmall")),
					   NULL);
    info->thumbnail = gdk_pixbuf_new_from_file (thumbnail_filename, NULL);
    g_free (path);
    if (info->thumbnail)
      info->thumbnail_filename = thumbnail_filename;
    else {
      info->thumbnail_filename = NULL;
      g_free (thumbnail_filename);
    }
  } else {
    info->thumbnail = NULL;
    info->thumbnail_filename = NULL;
  }

  if (json_object_has_member (obj, "linkUrl"))
    info->url = json_node_dup_string (json_object_get_member (obj, "linkUrl"));
  else
    info->url = g_strdup ("");

  return info;
}
