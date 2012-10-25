import gtk

class ShortcutCategoryBox(gtk.TreeView):
    def __init__(self, model):
        gtk.TreeView.__init__(self, model)

        self.set_headers_visible(False)
        self.set_property("show-expanders", False)
        self.set_property("level-indentation", 10)

        self.renderer = gtk.CellRendererText()
        self.column = gtk.TreeViewColumn('Column', self.renderer)

        def top_level(column, cell, store, iterator):
            cell.set_property("text", store[iterator][0])
            if store.iter_depth(iterator) == 0:
                cell.set_property('foreground', "black")
                cell.set_property('background', "gray")
            else:
                cell.set_property('foreground', "black")
                cell.set_property('background', "white")
        self.column.set_cell_data_func(self.renderer, top_level)

        self.append_column(self.column)

        self.selection = self.get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)
        self.selection.connect('changed', self.on_selection_changed)
        self.current = None

    def on_selection_changed(self, selection, data=None):
        model, iterator = selection.get_selected()
        
        if model.iter_depth(iterator) == 0 and iterator != self.current:
            self.collapse_all()
            self.expand_row(model.get_path(iterator), True)
            self.current = iterator
        # remove lines below after debugging is done
        selected_item = model.get_value(iterator, 0)
        print 'Should show items in', selected_item, 'category'