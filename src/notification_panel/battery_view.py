import gettext
import gtk
import datetime

from icon_plugin import IconPlugin
from panel_constants import PanelConstants
from ui.abstract_notifier import AbstractNotifier
from eos_widgets.desktop_transparent_window import DesktopTransparentWindow

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class BatteryView(AbstractNotifier, IconPlugin):
    X_OFFSET = 13
    WINDOW_WIDTH = 330
    WINDOW_HEIGHT = 160
    SMALLER_HEIGHT = 100
    WINDOW_BORDER = 10
    
    HORIZONTAL_MARGIN = 4
    
    POWER_SETTINGS = "power_settings"

    ICON_NAMES = ['battery_charging.png','battery_empty.png', 'battery_10.png', 'battery_25.png', 'battery_60.png', 'battery_full.png']
     
    _last_focus_out = datetime.datetime.min
    _focus_out_period = datetime.timedelta(milliseconds=250)

    def __init__(self, parent, icon_size):
        super(BatteryView, self).__init__(icon_size, self.ICON_NAMES, None)
       
        self.set_margin(self.HORIZONTAL_MARGIN)

        self._window = None

        self._parent = parent
        self._percentage_label = gtk.Label()
        self._time_to_depletion_label= gtk.Label()
        self._parent.connect("expose-event", self._draw)

    def display_battery(self, level, time_to_depletion, charging):
        self._level = level
        self._time_to_depletion = time_to_depletion 
        self._charging = charging 
        
        self._parent.set_visible_window(False)
        self._parent.set_size_request(PanelConstants.get_icon_size() + 2 * self.HORIZONTAL_MARGIN, PanelConstants.get_icon_size())
        
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
        elif level < 15:
            self._set_index(2)    
        elif level < 30:
            self._set_index(3)
        elif level < 75:
            self._set_index(4)
        else:
            self._set_index(5)
        
    def _create_menu(self):
        self._button_power_settings = gtk.Button(_('Power Settings'))
        self._button_power_settings.connect('button-press-event',
                lambda w, e: self._notify(self.POWER_SETTINGS))

        self._vbox = gtk.VBox()
        self._vbox.set_border_width(10)
        self._vbox.set_focus_chain([])
        self._vbox.add(self._button_power_settings)
        self._vbox.add(self._percentage_label)

        # Since the battery status dialog is resized dynamically,
        # for now we will simply grab the entire desktop background.
        # This is wasteful and could be optmized further.
        self._window = DesktopTransparentWindow(self._parent.get_toplevel())
        
        # Set up the window so that it can be exposed
        # with a transparent background and triangle decoration
        self._window.connect('expose-event', self._expose)
        self._window.connect('focus-out-event', lambda w, e: self.hide_window())
        self._window.set_border_width(self.WINDOW_BORDER)
        self._window.set_keep_above(False)
        self._window.set_name(_('Battery Info'))
        self._window.set_title(_('Battery Info'))

        screen = gtk.gdk.Screen() #@UndefinedVariable
        screen.connect('size-changed', lambda s: self._resize_occurred)

        # Place the widget in an event box within the window
        # (which has a different background than the transparent window)
        self._container = gtk.EventBox()

        self._vbox.show()
        self._container.add(self._vbox)
        self._window.add(self._container)
        
    def _resize_occurred(self):
        self._window.destroy()
        self._window = None
        
    def _remove_if_exists(self, component):
        found = False
        for child in self._vbox.get_children():
            found |= (child == component)
        if found:
            self._vbox.remove(component)

    def display_menu(self, level, time):
        # If we just had the focus out event (within the focus out period),
        # don't display the menu, as it was most likely due to clicking
        # on the battery icon to close the menu.
        if (datetime.datetime.now() - BatteryView._last_focus_out) < BatteryView._focus_out_period:
            return
        
        # In order to ensure we read the current background for the transparency,
        # let's always re-create the menu here.
        # TODO this could be handled more cleanly,
        # but for now just fixing the issue with minimal impact to existing code
        # if not self._window:
        #     self._create_menu()
        if self._window:
            self._window.destroy()
        self._create_menu()

        if self._window.get_visible():
            self._window.show_now()
            return

        self._percentage_label.set_text(str(level)+'%')
        self._remove_if_exists(self._time_to_depletion_label)

        desktop_size = self._parent.get_toplevel().get_size()    
        x = desktop_size[0] - self.WINDOW_WIDTH - self.X_OFFSET
        y = PanelConstants.DEFAULT_POPUP_VERTICAL_MARGIN

        height = 0
        if time:
            if self._charging:
                suffix = _(' until full')
            else:  
                suffix = _(' remaining')

            self._time_to_depletion_label.set_text(time+suffix)
            self._vbox.add(self._time_to_depletion_label)
            height = self.WINDOW_HEIGHT
        else:
            height = self.SMALLER_HEIGHT

        self._window.set_location((x, y))
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
        # Keep track of when the focus out event occurred most recently
        BatteryView._last_focus_out = datetime.datetime.now()
        
        self._window.set_visible(False)
        self._window.hide()
