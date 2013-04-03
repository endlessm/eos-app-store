import cairo
import gtk

class TransparentWindow(gtk.Window):
    def __init__(self, parent, background, location=(0,0), size=None, gradient_type=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.set_decorated(False)

        # Makes the window paintable, so we can draw directly on it
        self.set_app_paintable(True)
        self.set_size_request(width, height)

        # This sets the windows colormap, so it supports transparency.
        # This will only work if the wm support alpha channel
        screen = self.get_screen()
        rgba = self.get_rgba_colormap()
        self.set_colormap(rgba)
        
        self.gradient_type = gradient_type
        
        self.set_property("accept-focus", True)
        self.set_property("destroy-with-parent", True)
        self.set_property("focus-on-map", True)

        self.connect("expose-event", self._handle_event)
        
    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()
        
        cr.set_source_rgba(0, 0, 0, 255)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        self.draw(cr)

        return False

    def draw(self, cr):
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
    
