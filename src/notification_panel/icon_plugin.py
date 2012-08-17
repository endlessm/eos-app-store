import gtk
from gtk import gdk

from util.image_util import load_pixbuf
import cairo

class IconPlugin(gtk.EventBox):
    SHADOW_OFFSET = 1
    
    def __init__(self, icon_size, icon_name, command):
        super(IconPlugin, self).__init__()
        
        self.set_visible_window(False)
        
        self._command = command
        
        self.set_size_request(icon_size, icon_size)
        
        pixbuf = load_pixbuf(icon_name)
        self._scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        
        del pixbuf
        
        self.connect("expose-event", self._draw)
        self.connect("configure-event", self._draw)
        
    def get_launch_command(self):
        return self._command
    
    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        
        # Draw shadow
        cr.set_source_pixbuf(self._scaled_pixbuf, event.area.x + self.SHADOW_OFFSET, event.area.y + self.SHADOW_OFFSET)
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.paint_with_alpha(0.3)

        # Draw icon
        cr.set_source_pixbuf(self._scaled_pixbuf, event.area.x, event.area.y)
        cr.set_operator(cairo.OPERATOR_ATOP);
        cr.paint()
        
        return False
    
    