import gtk
import cairo
import math

from ui.abstract_notifier import AbstractNotifier
from util.transparent_window import TransparentWindow
from notification_panel_config import NotificationPanelConfig
from panel_constants import PanelConstants
from notification_plugin import NotificationPlugin
from util import screen_util

class BatteryView(AbstractNotifier):
    X_OFFSET = 27
    Y_LOCATION = 37
    WINDOW_WIDTH = 330
    WINDOW_HEIGHT = 160
    SMALLER_HEIGHT = 100
    WINDOW_BORDER = 10
    
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    GOLDEN_RATIO = 1.618
    
    BATTERY_FILL_MARGIN = 1
    ARC_OVERLAP = 0.3
    PLUG_VERTICAL_MARGIN = 3.3
    PRONG_SEPARATION_RATIO = 2.2
    
    FONT_SIZE = 9
    POWER_SETTINGS = "power_settings"

    def __init__(self, parent):
        self._parent = parent
        self._percentage_label = gtk.Label()
        self._time_to_depletion_label= gtk.Label()
        self._parent.connect("expose-event", self._draw)
        
    def display_battery(self, level, time_to_depletion, charging):
        self._level = level
        self._time_to_depletion = time_to_depletion 
        self._charging = charging 
        self._parent.set_visible_window(False)
        self._parent.set_size_request(PanelConstants.get_icon_size() + self.LEFT_MARGIN + self.RIGHT_MARGIN, PanelConstants.get_icon_size())
        self._recalculate_battery_bounds()
        self._parent.queue_draw()
        
    def _draw(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()
        
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width, event.area.height)
        cr.clip()
        
        cr.set_line_width(1);

        self._vertical_midpoint = event.area.y + event.area.height / 2
        self._horizontal_midpoint = event.area.x + event.area.width / 2
        self._battery_position_x = event.area.x + self.LEFT_MARGIN
        
        if self._level:
            self._draw_battery_with_shadow(cr, self._battery_position_x, self._vertical_midpoint)
            if self._charging:
                self._draw_outlet_cord_with_shadow(cr, self._horizontal_midpoint, self._vertical_midpoint, self._battery_base_height)
            else:
                self._draw_battery_level(cr, self._battery_position_x, self._vertical_midpoint)
        else:
            self._draw_outlet_cord_with_shadow(cr, self._horizontal_midpoint, self._vertical_midpoint, self._battery_base_height)
            
        cr.restore()
        
        return False
    
    def _draw_battery_with_shadow(self, cairo_context, position_x, vertical_midpoint):
        cairo_context.set_line_width(1);
        cairo_context.set_operator(cairo.OPERATOR_DEST_OUT);
        cairo_context.set_source_rgba(0.0, 0.0, 0.0, NotificationPanelConfig.SHADOW_ALPHA);
        self._draw_battery(cairo_context, position_x + NotificationPlugin.SHADOW_OFFSET, vertical_midpoint + NotificationPlugin.SHADOW_OFFSET)
        
        self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)  
        cairo_context.set_operator(cairo.OPERATOR_ATOP)
        self._draw_battery(cairo_context, position_x, vertical_midpoint)
    
    def _draw_battery_level(self, cairo_context, position_x, vertical_midpoint):
        if self._level:
            battery_percentage = self._level / 100.0
            self._set_color(cairo_context, PanelConstants.DEFAULT_PLUGIN_FG_COLOR)  
            if (battery_percentage < 0.10):
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
        self._draw_outlet_cord(cairo_context, horizontal_midpoint - self._battery_top_width / 2 + NotificationPlugin.SHADOW_OFFSET, vertical_midpoint + NotificationPlugin.SHADOW_OFFSET, self._battery_base_height)        

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
        red = int(color[1:3], 16) / 256.0
        green = int(color[3:5], 16) / 256.0
        blue = int(color[5:7], 16) / 256.0
        
        cairo_context.set_source_rgb(red, green, blue);    
    
    def _recalculate_battery_bounds(self):
        self._battery_base_width = PanelConstants.get_icon_size() * .85
        self._battery_base_height = self._battery_base_width * (1 / self.GOLDEN_RATIO)
        
        self._battery_top_width = PanelConstants.get_icon_size() - self._battery_base_width
        self._battery_top_height = self._battery_base_height / self.GOLDEN_RATIO
    
    def _create_menu(self):
        self._button_power_settings = gtk.Button(_('Power Settings'))
        self._button_power_settings.connect('button-press-event', 
                lambda w, e: self._notify(self.POWER_SETTINGS))

        self._vbox = gtk.VBox()
        self._vbox.set_border_width(10)
        self._vbox.set_focus_chain([])
        self._vbox.add(self._button_power_settings)
        self._vbox.add(self._percentage_label)
        
        self._window = TransparentWindow(self._parent.get_toplevel())
        # Set up the window so that it can be exposed
        # with a transparent background and triangle decoration
        self._window.connect('expose-event', self._expose)
        self._window.connect('focus-out-event', lambda w, e: self.hide_window())
        self._window.set_border_width(self.WINDOW_BORDER)
        self._window.set_keep_above(False)
        self._window.set_name(_('Battery Info'))
        self._window.set_title(_('Battery Info'))

        # Place the widget in an event box within the window
        # (which has a different background than the transparent window)
        self._container = gtk.EventBox()
        
        self._vbox.show()
        self._container.add(self._vbox)
        self._window.add(self._container)
        
    def _remove_if_exists(self, component):
        found = False
        for child in self._vbox.get_children():
            found |= (child == component)
        if found:    
            self._vbox.remove(component)
    
    def display_menu(self, level, time):
        if not hasattr(self, '_window'):
            self._create_menu()
        
        if self._window.get_visible():
            self._window.show_now()
            return 
                
        self._percentage_label.set_text(str(level)+'%')
        self._remove_if_exists(self._time_to_depletion_label)

        x = screen_util.get_width() - self.WINDOW_WIDTH - self.X_OFFSET
    
        # Get the x location of the center of the widget (icon), relative to the settings window
        height = 0
        if time:
            if self._charging:
                suffix = _(' min to charge fully')
            else:  
                suffix = _(' min left until empty')
            self._time_to_depletion_label.set_text(time+suffix)
            self._vbox.add(self._time_to_depletion_label)
            height = self.WINDOW_HEIGHT
        else: 
            height = self.SMALLER_HEIGHT

        self._window.move(x, self.Y_LOCATION)
        self._window.set_size_request(self.WINDOW_WIDTH, height)
        
        self._window.show_all()
        self.display()
        
    # TODO make the triangle position configurable
    def _expose(self, widget, event):
        cr = widget.window.cairo_create()

        # Decorate the border with a triangle pointing up
        # Use the same color as the default event box background
        # TODO eliminate need for these "magic" numbers
        cr.set_source_rgba(0xf2/255.0, 0xf1/255.0, 0xf0/255.0, 1.0)
        self._pointer = 110
        cr.move_to(self._pointer, 0)
        cr.line_to(self._pointer + 10, 10)
        cr.line_to(self._pointer - 10, 10)
        cr.fill()
        return False

    def display(self):
        self._window.set_visible(True)
        self._window.present()
        self._window.set_focus(self._window)

    def hide_window(self):
        self._window.set_visible(False)
        self._window.hide()
