#include "config.h"

#include "eos-app-utils.h"

#include <locale.h>
#include <glib/gi18n.h>

#define APP_STORE_CONTENT_DIR   "application-store"

/* Keep in the same order as the EosAppCategory enumeration */
static const struct {
  const EosAppCategory category;
  const char *directory;
} categories[] = {
  /* Translators: use the same string used to install the app store content JSON */
  { EOS_APP_CATEGORY_FEATURED,  N_("Featured") },
  { EOS_APP_CATEGORY_EDUCATION, N_("Education") },
  { EOS_APP_CATEGORY_LEISURE,   N_("Leisure") },
  { EOS_APP_CATEGORY_UTILITIES, N_("Utilities") },
};

static const char *
get_category_dir (EosAppCategory category)
{
  g_assert (category >= EOS_APP_CATEGORY_FEATURED &&
            category <= EOS_APP_CATEGORY_UTILITIES);

  return gettext (categories[category].directory);
}

/**
 * eos_app_get_content_dir:
 *
 * Retrieves the directory with the content for the given category, taking into account
 * the system locale.
 *
 * Returns: (transfer full):
 */
char *
eos_app_get_content_dir (EosAppCategory category)
{
  char *locale = setlocale (LC_MESSAGES, NULL);

  return g_build_filename (DATADIR,
                           APP_STORE_CONTENT_DIR,
                           locale,
                           get_category_dir (category),
                           NULL);
}
