import gtk
class BaseDesktop(gtk.VBox):
    def __init__(self):
        super(BaseDesktop, self).__init__(False, 3)

        self._top_taskbar_padding = None
        self._taskbar_widget = None
        self._icon_holder_widget = None
        
    def get_taskbar(self):
        return self._taskbar_widget

#    def get_searchbar(self):
#        return self._searchbar_widget
    
    def get_taskbar_padding(self):
        return self._taskbar_padding_widget
    
#    def get_searchbar_padding(self):
#        return self._searchbar_padding_widget
    
    def get_icon_holder(self):
        return self._icon_holder_widget
    
    def set_taskbar_widget(self, taskbar_widget):
        self._remove_child(self._taskbar_widget)
        self._remove_child(self._top_taskbar_padding)
        
        self._taskbar_widget = taskbar_widget
        self._top_taskbar_padding = gtk.HBox()

        width, height = self._taskbar_widget.size_request()
        import sys
        print >> sys.stderr, self._taskbar_widget.size_request()
        self._top_taskbar_padding.set_size_request(width, height)
        
        self.pack_start(self._taskbar_widget, False, False, 0)
        self.pack_end(self._top_taskbar_padding, False, False, 0)
        
    def set_icon_holder_widget(self, icon_holder_widget):
        self._remove_child(self._icon_holder_widget)
        
        self._icon_holder_widget = icon_holder_widget
        self.pack_start(self._icon_holder_padding_widget, True, True, 0)
        
    # Private methods
    def _remove_child(self, child):
        if child:
            self.remove(child)
            child.destroy()
