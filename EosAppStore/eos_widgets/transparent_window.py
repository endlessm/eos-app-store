import cairo
from gi.repository import Gtk

class TransparentWindow(Gtk.Window):
    def __init__(self, parent, background, location=(0,0), size=None, gradient_type=None):
        Gtk.Window.__init__(self, Gtk.WINDOW_TOPLEVEL)

        self.set_decorated(False)

        self.set_app_paintable(True)
        self.set_size_request(width, height)

        screen = self.get_screen()
        rgba = self.get_rgba_colormap()
        self.set_colormap(rgba)
        
        self.gradient_type = gradient_type
        
        self.set_property("accept-focus", True)
        self.set_property("destroy-with-parent", True)
        self.set_property("focus-on-map", True)

        self.connect("draw", self._handle_event)
        
    def _handle_event(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 255)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        self.draw(cr)

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
        super(Gtk.Window, self).destroy()
    
