import gtk
from ui.padding_widget import PaddingWidget

class BaseDesktop(gtk.VBox):
    def __init__(self):
        super(BaseDesktop, self).__init__(False, 3)

        self._top_taskbar_padding = None
        self._taskbar_widget = None
        self._main_content_widget = None
        
    def get_taskbar(self):
        return self._taskbar_widget

#    def get_searchbar(self):
#        return self._searchbar_widget
    
    def get_taskbar_padding(self):
        return self._taskbar_padding_widget
    
#    def get_searchbar_padding(self):
#        return self._searchbar_padding_widget
    
    def get_main_content(self):
        return self._main_content_widget
    
    def set_taskbar_widget(self, taskbar_widget):
        self._remove_child(self._taskbar_widget)
        self._remove_child(self._top_taskbar_padding)
        
        self._taskbar_widget = taskbar_widget
        self._top_taskbar_padding = PaddingWidget(outline=True)
        self._top_taskbar_padding.set_size_request(1600,250)

        self.pack_end(self._taskbar_widget, False, False, 0)

        width = self._taskbar_widget.allocation.width
        height = self._taskbar_widget.allocation.height
        import sys
        print >> sys.stderr, width, height
#self._top_taskbar_padding.set_size_request(width, height)
        
        self.pack_start(self._top_taskbar_padding, False, False, 0)
        
    def set_main_content_widget(self, main_content_widget):
        self._remove_child(self._main_content_widget)
        
        self._main_content_widget = main_content_widget
        self.pack_start(self._main_content_widget, True, True, 0)
        
    # Private methods
    def _remove_child(self, child):
        if child:
            self.remove(child)
            child.destroy()
