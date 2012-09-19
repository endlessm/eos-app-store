import cairo
import gtk
from gtk import gdk
from util import image_util, screen_util

class TransparentWindow(gtk.Window):
    def __init__(self, parent):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_wmclass("endless_os_desktop", "modal")

        self.set_property("accept-focus", True)
        self.set_property("destroy-with-parent", True)
        self.set_property("focus-on-map", True)
        
        self.set_transient_for(parent)
        
        self.set_can_focus(True)
        self.set_can_default(True)

        self.connect("expose-event", self._handle_event)
        self._background = image_util.load_pixbuf("background.png")
        
        self._background = self._background.scale_simple(screen_util.get_width(), screen_util.get_height(),gtk.gdk.INTERP_BILINEAR)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_decorated(False)

    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()
        x,y = self.window.get_origin()
        
        cr.set_source_rgba(0, 0, 0, 255);
        cr.set_operator(cairo.OPERATOR_SOURCE);
        cr.paint()
        
        self.draw(cr, x,y)
        
        self.show_all()
        
        return False
        
    def draw(self, cr, x, y):
        w, h = self.size_request()
        pixbuf = self._background.subpixbuf(x, y, w, h)
        cr.set_source_pixbuf(pixbuf, 0, 0)

        cr.paint()
        self.queue_draw()
        
        return False
