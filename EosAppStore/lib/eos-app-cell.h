#ifndef EOS_APP_CELL_H
#define EOS_APP_CELL_H

#include <gtk/gtk.h>
#include "eos-app-enums.h"
#include "eos-app-info.h"

G_BEGIN_DECLS

#define EOS_TYPE_APP_CELL       (eos_app_cell_get_type ())

typedef struct _EosAppCell      EosAppCell;
typedef struct _EosAppCellClass EosAppCellClass;

GType eos_app_cell_get_type (void);

GtkWidget *     eos_app_info_create_cell                (const EosAppInfo *info,
                                                         const gchar *icon_name);

gint            eos_app_info_get_cell_margin            (void);

G_END_DECLS

#endif /* EOS_APP_CELL_H */
