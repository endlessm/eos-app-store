/* Copyright 2013 Endless Mobile, Inc. */

#ifndef EOS_FLEXY_GRID_PRIVATE_H
#define EOS_FLEXY_GRID_PRIVATE_H

#include "eos-flexy-grid.h"

G_BEGIN_DECLS

void            eos_flexy_grid_cell_set_iter            (EosFlexyGridCell *cell,
                                                         GSequenceIter    *iter);
GSequenceIter * eos_flexy_grid_cell_get_iter            (EosFlexyGridCell *cell);
void            eos_flexy_grid_cell_set_selected        (EosFlexyGridCell *cell,
                                                         gboolean          selected);

G_END_DECLS

#endif /* EOS_FLEXY_GRID_PRIVATE_H */
