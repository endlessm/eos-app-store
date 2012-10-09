import gobject
import cairo

from battery_util import BatteryUtil
from notification_plugin import NotificationPlugin
from notification_panel_config import NotificationPanelConfig
from panel_constants import PanelConstants

class BatteryPlugin(NotificationPlugin):
    REFRESH_TIME = 30000
    
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    GOLDEN_RATIO = 1.618
    
    def __init__(self, icon_size, gobj = gobject):
        super(BatteryPlugin, self).__init__()
        self._icon_size=icon_size
        self.set_visible_window(False)
        
        self.set_size_request(icon_size + self.LEFT_MARGIN + self.RIGHT_MARGIN, icon_size)
        
        self._update_battery_indicator()

        self.connect("expose-event", self._draw)
        
        gobject.timeout_add(BatteryPlugin.REFRESH_TIME, self._update_battery_indicator)
        
    def _update_battery_indicator(self):
        self._battery_level = BatteryUtil.get_battery_level()
        self.queue_draw()
        
        return True

    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()
        
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        
        cr.set_line_width(1);

        battery_base_width = self._icon_size * .85
        battery_base_height = battery_base_width * (1 / self.GOLDEN_RATIO)
        
        battery_top_width = self._icon_size - battery_base_width
        battery_top_height= battery_base_height / self.GOLDEN_RATIO
        
        widget_vertical_midpoint = event.area.y +  event.area.height / 2
        
        # Draw shadow
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        
        cr.rectangle(event.area.x + self.LEFT_MARGIN + self.SHADOW_OFFSET, widget_vertical_midpoint + self.SHADOW_OFFSET - battery_base_height / 2, battery_base_width, battery_base_height);
        cr.rectangle(event.area.x + self.LEFT_MARGIN + self.SHADOW_OFFSET + battery_base_width, widget_vertical_midpoint + self.SHADOW_OFFSET - battery_top_height / 2, battery_top_width, battery_top_height);
        cr.stroke()

        # Draw icon
        self._set_color(cr, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)  
        cr.set_operator(cairo.OPERATOR_ATOP)
        
        cr.rectangle(event.area.x + self.LEFT_MARGIN, widget_vertical_midpoint - battery_base_height / 2, battery_base_width, battery_base_height);
        cr.rectangle(event.area.x + self.LEFT_MARGIN + battery_base_width, widget_vertical_midpoint - battery_top_height / 2, battery_top_width, battery_top_height);
        cr.stroke()
        
        if self._battery_level is not None:
            battery_percentage = self._battery_level / 100.0
            self._set_color(cr, PanelConstants.DEFAULT_PLUGIN_OK_COLOR)  
            if (battery_percentage < 0.50):
                self._set_color(cr, PanelConstants.DEFAULT_PLUGIN_WARN_COLOR)
            if (battery_percentage < 0.25):
                self._set_color(cr, PanelConstants.DEFAULT_PLUGIN_CAUTION_COLOR)
                
            cr.rectangle(event.area.x + self.LEFT_MARGIN + 1, widget_vertical_midpoint - battery_base_height / 2 + 1, (battery_base_width - 2) * battery_percentage , battery_base_height - 2);
            cr.fill()
        
        cr.restore()
        
        return False

    def _set_color(self, cairo_context, color):
        red =   int(color[1:3], 16) / 256.0
        green = int(color[3:5], 16) / 256.0
        blue =  int(color[5:7], 16) / 256.0
        
        cairo_context.set_source_rgb(red, green, blue);  
        
