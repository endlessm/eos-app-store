import gtk
from ui.padding_widget import PaddingWidget

class BaseDesktop(gtk.VBox):
    def __init__(self):
        super(BaseDesktop, self).__init__(False, 3)

        self._top_page_padding_widget = None
        self._taskbar_widget = None
        self._searchbar_widget = None
        self._main_content_widget = None
        
    def get_main_content(self):
        return self._main_content_widget
    
    def set_taskbar_widget(self, taskbar_widget):
        self._remove_child(self._taskbar_widget)
        self._remove_child(self._top_page_padding_widget)
        
        self._taskbar_widget = taskbar_widget
        self._top_page_padding_widget = PaddingWidget()

        self.pack_end(self._taskbar_widget, False, False, 0)
        self.pack_start(self._top_page_padding_widget, False, False, 0)

    def set_searchbar_widget(self, searchbar_widget):
        self._remove_child(self._searchbar_widget)
        
        self._searchbar_widget = searchbar_widget
        self.pack_end(self._searchbar_widget, False, False, 0)

    def set_page_buttons_widget(self, widget):
        self._page_buttons_widget = widget
        self.pack_end(self._page_buttons_widget, False, False, 0)

    def get_page_buttons_widget(self):
        return self._page_buttons_widget

    def recalculate_padding(self, icon_layout):
        middle_point = self._calculate_middle_point(icon_layout)
        self._searchbar_widget.set_size_request(0, middle_point)

        taskbar_width = self._taskbar_widget.allocation.width

        taskbar_height = self._taskbar_widget.allocation.height
        searchbar_height = self._searchbar_widget.size_request()[1]
        page_buttons_height = self._page_buttons_widget.size_request()[1] 
        total_top_padding = taskbar_height + searchbar_height + page_buttons_height

        self._top_page_padding_widget.set_size_request(taskbar_width, total_top_padding)

    def set_main_content_widget(self, main_content_widget):
        self._remove_child(self._main_content_widget)
        
        self._main_content_widget = main_content_widget
        self.pack_start(self._main_content_widget, True, True, 0)
        
    # Private methods
    def _calculate_middle_point(self, icon_layout):
        import sys
        icon_layout_bottom = self._get_absolute_y(icon_layout) + icon_layout.size_request()[1]
        print >> sys.stderr, "layout_bottom", icon_layout_bottom

        window_coords = self._taskbar_widget.window.get_root_origin()[1]
        widget_coords = self._taskbar_widget.translate_coordinates(self._taskbar_widget.get_toplevel(), 0, 0)[1]
        taskbar_top = window_coords + widget_coords
        print >> sys.stderr, "taskbar top", taskbar_top
        page_buttons_height = self._page_buttons_widget.size_request()[1] 
        print >> sys.stderr, "page buttons height", page_buttons_height

        return (taskbar_top - icon_layout_bottom - page_buttons_height) / 2

    def _get_absolute_y(self, widget):
        import sys
        window_coords = widget.window.get_root_origin()[1]
        print >> sys.stderr, "layout_win_coords", window_coords

        widget_coords = widget.translate_coordinates(widget.get_toplevel(), 0, 0)[1]
        print >> sys.stderr, "layout_widget_coords", widget_coords, widget.get_toplevel()
        return window_coords + widget_coords

    def _remove_child(self, child):
        if child:
            self.remove(child)
            child.destroy()
