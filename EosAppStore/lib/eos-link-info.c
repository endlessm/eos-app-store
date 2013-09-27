#include "config.h"

#include "eos-link-info.h"
#include "eos-app-utils.h"

struct _EosLinkInfo
{
  volatile int ref_count;

  gchar *id;
  gchar *title;
  gchar *description;
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
  const gchar *path;
  gchar *thumbnail;

  g_return_val_if_fail (JSON_NODE_HOLDS_OBJECT (node), NULL);

  obj = json_node_get_object (node);
  info = eos_link_info_new ();

  if (json_object_has_member (obj, "linkId")) {
    info->id = json_node_dup_string (json_object_get_member (obj, "linkId"));
  } else {
    info->id = NULL;
  }

  if (json_object_has_member (obj, "linkName")) {
    info->title = json_node_dup_string (json_object_get_member (obj, "linkName"));
  } else {
    info->title = g_strdup ("");
  }

  if (json_object_has_member (obj, "linkSubtitle")) {
    info->description = json_node_dup_string (json_object_get_member (obj, "linkSubtitle"));
  } else {
    info->description = g_strdup ("");
  }

  if (json_object_has_member (obj, "linkSmall")) {
    path = eos_app_get_link_content_dir();
    thumbnail = g_build_filename (path,
				  json_node_dup_string (json_object_get_member (obj, "linkSmall")),
				  NULL);
    info->thumbnail = gdk_pixbuf_new_from_file (thumbnail, NULL);
    g_free (thumbnail);
  } else {
    info->thumbnail = NULL;
  }

  if (json_object_has_member (obj, "linkUrl")) {
    info->url = json_node_dup_string (json_object_get_member (obj, "linkUrl"));
  } else {
    info->url = g_strdup ("");
  }

  return info;
}
