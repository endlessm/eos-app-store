import gtk

import datetime
import gobject
import pango
import cairo

from notification_panel_config import NotificationPanelConfig
from notification_plugin import NotificationPlugin

class TimeDisplayPlugin(NotificationPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager datetime'
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    
    def __init__(self, icon_size):
        super(TimeDisplayPlugin, self).__init__(self.COMMAND)
        
        self._update_time()
        
        self.set_visible_window(False)
        
        self.connect("expose-event", self._draw)
        
        gobject.timeout_add(10000, self._update_time)
    
    def _update_time(self):
        try:
            date = datetime.datetime.now().strftime('%b %d | %H:%M %p').upper()

            attributes = pango.parse_markup('<span color="#f6f6f6" size="large" weight="bold">' + date + '</span>', u'\x00')[0]
            self._text_layout = self.create_pango_layout(date)
            self._text_layout.set_attributes(attributes)
            
            shadow_attributes = pango.parse_markup('<span size="large" weight="bold">' + date + '</span>', u'\x00')[0]
            self._shadow_layout = self.create_pango_layout(date)
            self._shadow_layout.set_attributes(shadow_attributes)

            text_size_x, text_size_y = self._text_layout.get_pixel_size()
            self.set_size_request(text_size_x + self.SHADOW_OFFSET + self.LEFT_MARGIN + self.RIGHT_MARGIN, text_size_y + self.SHADOW_OFFSET)
            
            self.queue_draw()
        except:
            pass
        
        return True
        
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

        cr.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        cr.move_to(widget_area.x + self.SHADOW_OFFSET + self.LEFT_MARGIN, widget_area.y + self.SHADOW_OFFSET)
        
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.show_layout(self._shadow_layout)

        cr.move_to(widget_area.x + self.LEFT_MARGIN, widget_area.y)
        cr.set_operator(cairo.OPERATOR_ATOP);
        cr.show_layout(self._text_layout)
        
        cr.restore()
        return False
