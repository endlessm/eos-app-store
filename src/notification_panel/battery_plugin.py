import gobject
import cairo

from battery_util import BatteryUtil
from notification_plugin import NotificationPlugin
from notification_panel_config import NotificationPanelConfig
from panel_constants import PanelConstants
import math
import pango

class BatteryPlugin(NotificationPlugin):
    COMMAND = "gksudo gnome-control-center power"
    
    REFRESH_TIME = 5000
    BATTERY_AVAILABILITY_REFRESH_TIME = 10000
    
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    GOLDEN_RATIO = 1.618
    
    BATTERY_FILL_MARGIN = 1
    BATTERY_TEXT_MARGIN = 2
    ARC_OVERLAP = 0.3
    PLUG_VERTICAL_MARGIN = 3.3
    PRONG_SEPARATION_RATIO = 2.2
    
    FONT_SIZE = 9
    
    def __init__(self, icon_size, gobj = gobject):
        super(BatteryPlugin, self).__init__(self.COMMAND)
        self._icon_size=icon_size
        self.set_visible_window(False)
        
        self._poll_for_battery()
        gobject.timeout_add(BatteryPlugin.BATTERY_AVAILABILITY_REFRESH_TIME, self._poll_for_battery)
        
    def _poll_for_battery(self):
        if BatteryUtil.get_battery_level()[0]:
            self._start_battery_polling()
        
        return True
        
    def _start_battery_polling(self):
        self.set_size_request(self._icon_size + self.LEFT_MARGIN + self.RIGHT_MARGIN, self._icon_size)
        
        self._update_battery_indicator()

        self.connect("expose-event", self._draw)
        
        gobject.timeout_add(BatteryPlugin.REFRESH_TIME, self._update_battery_indicator)
        
    def _update_battery_indicator(self):
        self._recalculate_battery_bounds()
        self._battery_level, self._is_recharging = BatteryUtil.get_battery_level()
        self.queue_draw()
        return True
    
    def _recalculate_battery_bounds(self):
        self._battery_base_width = self._icon_size * .85
        self._battery_base_height = self._battery_base_width * (1 / self.GOLDEN_RATIO)
        
        self._battery_top_width = self._icon_size - self._battery_base_width
        self._battery_top_height= self._battery_base_height / self.GOLDEN_RATIO

    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()
        
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        
        cr.set_line_width(1);

        vertical_midpoint = event.area.y + event.area.height / 2
        horizontal_midpoint = event.area.x + event.area.width / 2
        battery_position_x = event.area.x + self.LEFT_MARGIN
        
        # Battery Level text
        self._draw_battery_with_shadow(cr, battery_position_x, vertical_midpoint)

        if self._battery_level:
            self._draw_battery_level(cr, battery_position_x, vertical_midpoint)
        
#        if self._is_recharging:
#            self._draw_outlet_cord_with_shadow(cr, horizontal_midpoint, vertical_midpoint, self._battery_base_height)        
        self._show_battery_text(cr, battery_position_x, vertical_midpoint)
        cr.restore()
        
        return False
    
    def _show_battery_text(self, cairo_context, position_x, vertical_midpoint):
        self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)
        cairo_context.move_to(position_x + self.BATTERY_TEXT_MARGIN, vertical_midpoint + (self.FONT_SIZE/3.2))
        cairo_context.set_font_size(self.FONT_SIZE)
        cairo_context.show_text(str(self._battery_level))
    
    def _draw_battery_with_shadow(self, cairo_context, position_x, vertical_midpoint):
        cairo_context.set_line_width(1);
        cairo_context.set_operator(cairo.OPERATOR_DEST_OUT);
        cairo_context.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        self._draw_battery(cairo_context, position_x + self.SHADOW_OFFSET, vertical_midpoint + self.SHADOW_OFFSET)
        
        self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)  
        cairo_context.set_operator(cairo.OPERATOR_ATOP)
        self._draw_battery(cairo_context, position_x, vertical_midpoint)
    
    def _draw_battery_level(self, cairo_context, position_x, vertical_midpoint):
        battery_percentage = self._battery_level / 100.0
        self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_OK_COLOR)  
        if (battery_percentage < 0.50):
            self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_WARN_COLOR)
        if (battery_percentage < 0.25):
            self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_CAUTION_COLOR)
            
        cairo_context.rectangle(position_x + self.BATTERY_FILL_MARGIN, vertical_midpoint - self._battery_base_height / 2 + self.BATTERY_FILL_MARGIN, (self._battery_base_width - 2 * self.BATTERY_FILL_MARGIN) * battery_percentage , self._battery_base_height - (self.BATTERY_FILL_MARGIN * 2))
        cairo_context.fill()
    
    def _draw_battery(self, cairo_context, position_x, vertical_midpoint):
        # Battery base
        cairo_context.rectangle(position_x, vertical_midpoint - self._battery_base_height / 2, self._battery_base_width, self._battery_base_height);
        # Battery top
        cairo_context.rectangle(position_x + self._battery_base_width, vertical_midpoint - self._battery_top_height / 2, self._battery_top_width, self._battery_top_height);

        cairo_context.stroke()
    
    def _draw_outlet_cord_with_shadow(self, cairo_context, horizontal_midpoint, vertical_midpoint, height):
        cairo_context.set_line_width(1);
        cairo_context.set_operator(cairo.OPERATOR_DEST_OUT);
        cairo_context.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        self._draw_outlet_cord(cairo_context, horizontal_midpoint - self._battery_top_width / 2 + self.SHADOW_OFFSET, vertical_midpoint + self.SHADOW_OFFSET, self._battery_base_height)        

        cairo_context.set_operator(cairo.OPERATOR_ATOP);
        self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)
        self._draw_outlet_cord(cairo_context, horizontal_midpoint - self._battery_top_width / 2, vertical_midpoint, self._battery_base_height)        
        
    
    def _draw_outlet_cord(self, cairo_context, midpoint_x, midpoint_y, height):
        arc_radius = height - self.PLUG_VERTICAL_MARGIN * 2
        
        # Cord holder
        cairo_context.arc(midpoint_x + arc_radius / 2, midpoint_y, arc_radius, math.pi / 2 - self.ARC_OVERLAP, 1.5 * math.pi + self.ARC_OVERLAP)
        cairo_context.fill()

        # Bottom prong
        cairo_context.set_line_width(2);
        cairo_context.move_to(midpoint_x + arc_radius / 2, midpoint_y + arc_radius / self.PRONG_SEPARATION_RATIO);
        cairo_context.line_to(midpoint_x + arc_radius * 1.5, midpoint_y + arc_radius / self.PRONG_SEPARATION_RATIO);
        cairo_context.stroke()
        
        # Top prong
        cairo_context.move_to(midpoint_x + arc_radius / 2, midpoint_y - arc_radius / self.PRONG_SEPARATION_RATIO);
        cairo_context.line_to(midpoint_x + arc_radius * 1.5, midpoint_y - arc_radius / self.PRONG_SEPARATION_RATIO);
        cairo_context.stroke()
        
        # Cord
        cairo_context.move_to(midpoint_x + arc_radius / 2, midpoint_y);
        cairo_context.line_to(midpoint_x - arc_radius * 1.5, midpoint_y);
        cairo_context.stroke()       

    def _set_color(self, cairo_context, color):
        red =   int(color[1:3], 16) / 256.0
        green = int(color[3:5], 16) / 256.0
        blue =  int(color[5:7], 16) / 256.0
        
        cairo_context.set_source_rgb(red, green, blue);  
        
