import gtk
import cairo
from gtk import gdk

from eos_util.image_util import load_pixbuf
from notification_panel_config import NotificationPanelConfig
from notification_plugin import NotificationPlugin

class IconPlugin(NotificationPlugin):

    # TODO Properly center vertically within taskbar; for now, we hard-code an offset
    CENTER_Y_OFFSET = 9
    
    def __init__(self, icon_size, icon_names, command, init_index = 0):
        super(IconPlugin, self).__init__(command)

        self.set_visible_window(False)
        self.set_size_request(icon_size, icon_size)
        self._horizontal_margin = 0
        
        self._icon_size = icon_size        
        self._scaled_pixbufs = [None] * len(icon_names)

        index = 0
        for icon_name in icon_names:
            pixbuf = load_pixbuf(icon_name)
            self._scaled_pixbufs[index] = pixbuf
            index += 1

            del pixbuf

        self._set_index(init_index)

        self.connect("expose-event", self._draw)
        
    def set_margin(self, horizontal_margin):
        self._horizontal_margin = horizontal_margin
        self.set_size_request(self._icon_size + 2 * self._horizontal_margin, self._icon_size)

    def _set_index(self, index):
        self._index = index

    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()

        # clip to dimensions of event region
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()

        # Need to draw relative to the area of the widget region
        # rather than the event region
        widget_area = widget.get_allocation()

        # Draw shadow
        cr.set_source_pixbuf(self._scaled_pixbufs[self._index], widget_area.x + self._horizontal_margin + self.SHADOW_OFFSET, widget_area.y + self.CENTER_Y_OFFSET + self.SHADOW_OFFSET)
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.paint_with_alpha(NotificationPanelConfig.SHADOW_ALPHA)

        # Draw icon
        cr.set_source_pixbuf(self._scaled_pixbufs[self._index], widget_area.x + self._horizontal_margin, widget_area.y + self.CENTER_Y_OFFSET)
        cr.set_operator(cairo.OPERATOR_ATOP);
        cr.paint()

        cr.restore()
        return False

