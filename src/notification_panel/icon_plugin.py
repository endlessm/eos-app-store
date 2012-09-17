import gtk
import cairo
from gtk import gdk

from util.image_util import load_pixbuf
from notification_panel_config import NotificationPanelConfig
from notification_plugin import NotificationPlugin

class IconPlugin(NotificationPlugin):
    
    def __init__(self, icon_size, icon_names, command, init_index = 0):
        super(IconPlugin, self).__init__(command)
        
        self.set_visible_window(False)
        
        self.set_size_request(icon_size, icon_size)
        
        self._scaled_pixbufs = [None] * len(icon_names)

        index = 0
        for icon_name in icon_names:
            pixbuf = load_pixbuf(icon_name)
            self._scaled_pixbufs[index] = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
            index += 1
        
            del pixbuf
        
        self._set_index(init_index)

        self.connect("expose-event", self._draw)
        
    def _set_index(self, index):
        self._index = index
    
    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()
        
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        # Draw shadow
        cr.set_source_pixbuf(self._scaled_pixbufs[self._index], event.area.x + self.SHADOW_OFFSET, event.area.y + self.SHADOW_OFFSET)
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.paint_with_alpha(NotificationPanelConfig.SHADOW_ALPHA)

        # Draw icon
        cr.set_source_pixbuf(self._scaled_pixbufs[self._index], event.area.x, event.area.y)
        cr.set_operator(cairo.OPERATOR_ATOP);
        cr.paint()
        
        cr.restore()
        return False

