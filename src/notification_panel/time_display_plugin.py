import gtk

import datetime
import gobject
import pango
import cairo
import locale

from notification_panel_config import NotificationPanelConfig
from notification_plugin import NotificationPlugin
from notification_plugin import NotificationPlugin
from time_display_plugin_model import TimeDisplayPluginModel

class TimeDisplayPlugin(NotificationPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager datetime'
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    
    def __init__(self, icon_size, time_display_plugin_model=TimeDisplayPluginModel()):
        super(TimeDisplayPlugin, self).__init__(self.COMMAND)
        
        self._update_time()
        
        self.set_visible_window(False)

        self._time_display_plugin_model = time_display_plugin_model
        
        self._update_time()
        gobject.timeout_add(10000, self._update_time)

        self.connect("expose-event", self._draw)
    
    def _update_time(self):
        try:
            date = self._time_display_plugin_model.get_date_text()

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
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        
        cr.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        cr.move_to(event.area.x + self.SHADOW_OFFSET + self.LEFT_MARGIN, event.area.y + self.SHADOW_OFFSET)
        
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.show_layout(self._shadow_layout)

        cr.move_to(event.area.x + self.LEFT_MARGIN, event.area.y)
        cr.set_operator(cairo.OPERATOR_ATOP);
        cr.show_layout(self._text_layout)
        
        cr.restore()
        return False
