import cairo
import gtk
from gtk import gdk
from util import image_util, screen_util

class TransparentWindow(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
#        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DESKTOP) #@UndefinedVariable
        self.connect("expose-event", self._handle_event)
        self.connect("configure-event", self._handle_event)
        self._background = image_util.load_pixbuf("background.png")
        
        self._background = self._background.scale_simple(screen_util.get_width(), screen_util.get_height(),gtk.gdk.INTERP_BILINEAR)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_decorated(False)

    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()
        x,y = self.window.get_origin()
        
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
