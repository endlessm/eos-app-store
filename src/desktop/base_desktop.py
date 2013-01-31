import gtk
from ui.padding_widget import PaddingWidget

class BaseDesktop(gtk.VBox):
    def __init__(self):
        super(BaseDesktop, self).__init__(False, 3)

        self._top_taskbar_padding = None
        self._taskbar_widget = None
        self._searchbar_widget = None
        self._top_searchbar_padding = None
        self._main_content_widget = None
        self._top_page_buttons_padding_widget = None
        
    def get_main_content(self):
        return self._main_content_widget
    
    def set_taskbar_widget(self, taskbar_widget):
        self._remove_child(self._taskbar_widget)
        self._remove_child(self._top_taskbar_padding)
        
        self._taskbar_widget = taskbar_widget
        self._top_taskbar_padding = PaddingWidget()

        self.pack_end(self._taskbar_widget, False, False, 0)
        self.pack_start(self._top_taskbar_padding, False, False, 0)

    def set_searchbar_widget(self, searchbar_widget):
        self._remove_child(self._searchbar_widget)
        self._remove_child(self._top_searchbar_padding)
        
        self._searchbar_widget = searchbar_widget
        self._top_searchbar_padding = PaddingWidget()

        self.pack_end(self._searchbar_widget, False, False, 0)
        self.pack_start(self._top_searchbar_padding, False, False, 0)

    def set_page_buttons_widget(self, widget):
        self._top_page_buttons_padding_widget = PaddingWidget()
        self._page_buttons_widget = widget

        self.pack_start(self._top_page_buttons_padding_widget, False, False, 0)
        self.pack_end(self._page_buttons_widget, False, False, 0)

    def get_page_buttons_widget(self):
        return self._page_buttons_widget

    def recalculate_padding(self):
        taskbar_width = self._taskbar_widget.allocation.width
        taskbar_height = self._taskbar_widget.allocation.height
        self._top_taskbar_padding.set_size_request(taskbar_width, taskbar_height)

        searchbar_width = self._searchbar_widget.allocation.width
        searchbar_height = self._searchbar_widget.allocation.height
        self._top_searchbar_padding.set_size_request(searchbar_width, searchbar_height)

        page_buttons_width = self._page_buttons_widget.allocation.width
        page_buttons_height = self._page_buttons_widget.allocation.height
        self._top_page_buttons_padding_widget.set_size_request(page_buttons_width, page_buttons_height)

        import sys
        print >> sys.stderr, page_buttons_height

    def set_main_content_widget(self, main_content_widget):
        self._remove_child(self._main_content_widget)
        
        self._main_content_widget = main_content_widget
        self.pack_start(self._main_content_widget, True, True, 0)
        
    # Private methods
    def _remove_child(self, child):
        if child:
            self.remove(child)
            child.destroy()
