import cairo
import gtk

class TransparentWindow(gtk.Window):
    def __init__(self, parent, background, location=(0,0), size=None, gradient_type=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self._background = background
        self.gradient_type = gradient_type
        self.set_wmclass("endless_os_desktop", "modal")

        self.set_property("accept-focus", True)
        self.set_property("destroy-with-parent", True)
        self.set_property("focus-on-map", True)

        self.set_transient_for(parent)

        self.set_can_focus(True)
        self.set_can_default(True)

        self.connect("expose-event", self._handle_event)
        
        self._origin_x, self._origin_y = parent.window.get_origin()
        
        self.set_location(location)
        
        self._background_x = self._x
        self._background_y = self._y
        
        if not size:
            size = parent.get_size()
        self._width, self._height = size

        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_has_frame(False)
        
        # Prevent gnome desktop (e.g. on developer setup)
        # from displaying an icon on the taskbar
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_POPUP_MENU)
        
        # Prevent our taksbar manager from displaying an icon
        self.set_skip_taskbar_hint(True)

    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()
        
        cr.set_source_rgba(0, 0, 0, 255)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        self.draw(cr)

        return False

    def draw(self, cr):
        self._background.draw(lambda pixbuf: cr.set_source_pixbuf(pixbuf,
                self._background_x - self._x,
                self._background_y - self._y))

        if self.gradient_type is None:
            cr.paint()
        else:
            gradient = cairo.LinearGradient(0, 0, 0, self._height)
            gradient.add_color_stop_rgba(0.005, 255, 255, 255, 0)
            gradient.add_color_stop_rgba(0.006, 0, 0, 0, 0.7)
            gradient.add_color_stop_rgba(0.994, 0, 0, 0, 0.0)
            gradient.add_color_stop_rgba(0.995, 255, 255, 255, 0)
            cr.mask(gradient)
            cr.fill()
        
        return False
    
    def set_location(self, location):
        self._x, self._y = location
        self.move(self._origin_x + self._x, self._origin_y + self._y)

    def set_size(self, size):
        self._width, self._height = size
    
    def destroy(self):
        try:
            del self._background
        except:
            pass
        super(gtk.Window, self).destroy()
    
