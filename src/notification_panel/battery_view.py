import gtk

from icon_plugin import IconPlugin
from panel_constants import PanelConstants
from ui.abstract_notifier import AbstractNotifier
from util import screen_util
from util.transparent_window import TransparentWindow

class BatteryView(AbstractNotifier, IconPlugin):
    X_OFFSET = 27
    Y_LOCATION = 37
    WINDOW_WIDTH = 330
    WINDOW_HEIGHT = 160
    SMALLER_HEIGHT = 100
    WINDOW_BORDER = 10
    
    LEFT_MARGIN = 3
    RIGHT_MARGIN = 3
    
    POWER_SETTINGS = "power_settings"

    ICON_NAMES = ['battery_charging.png','battery_empty.png', 'battery_15.png', 'battery_50.png', 'battery_full.png']
     
    def __init__(self, parent, icon_size):
        super(BatteryView, self).__init__(icon_size, self.ICON_NAMES, None)
        
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
        
        if self._level == None:
            self._parent.hide()
        else:
            self._parent.show()
            self._set_battery_image(self._level, self._charging)
            
            self.queue_draw()
            self._parent.queue_draw()
        
        

    def _set_battery_image(self, level, is_charging):
        if is_charging:
            self._set_index(0)
        elif level < 5:
            self._set_index(1)
        elif level < 25:
            self._set_index(2)
        elif level < 75:
            self._set_index(3)
        else:
            self._set_index(4)
        
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
