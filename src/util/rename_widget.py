import gtk

class RenameWidget:

    def __init__(self, presenter=None, x=250, y=300, caller=None, y_offset=0, caller_width=64, container=None):
        self.caller = caller
        self.original_name = caller._identifier
        self.x = x
        self.y = y + y_offset
        self.presenter = presenter
        self.container = container
        self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self._window.set_decorated(False)
        self._window.set_border_width(0)
        
        self.text_view = gtk.Entry()
        self.text_view.set_alignment(0.5)
        self.text_view.set_has_frame(False)
        self.text_view.set_editable(False)
        self.text_view.set_text(self.original_name)
        self.text_view.select_region(0, -1)
        t_width = self.text_view.get_layout().get_pixel_size()[0]
        if t_width <= caller_width:
            t_width = caller_width
        else:
            t_width += 5
        self._window.set_size_request(t_width, -1)
        self._window.add(self.text_view)
        self.text_view.connect("key-release-event", self._handle_key_press)
        self.text_view.connect("button-press-event", self._handle_click)
        self._window.connect("focus-out-event", self._handle_focus_out)
        self._window.move(self.x - (int((t_width - caller_width)/2)), self.y)
        self._window.show_all()
    
    def _handle_key_press(self, widget, event):
        if gtk.gdk.keyval_name(event.keyval) == 'Escape':
            self.destroy()
        elif gtk.gdk.keyval_name(event.keyval) == 'Return':
            new_name = self.text_view.get_text().strip()
            self._save_new_name(new_name)
    
    def _handle_click(self, widget, event):
        self.text_view.set_editable(True)
    
    def _handle_focus_out(self, widget, event):
        new_name = self.text_view.get_text().strip()
        self._save_new_name(new_name)
        
    def _save_new_name(self, new_name):
        self.caller.rename_shortcut(new_name)
        self.destroy()
    
    def destroy(self):
        self._window.destroy()