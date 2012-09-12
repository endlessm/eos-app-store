import gtk
import gtk.gdk
import cairo

class NotificationPlugin(gtk.EventBox):
    SHADOW_OFFSET = 1
    
    # In the current design, all the notification windows
    # have the same width, and the height will grow as needed
    WINDOW_WIDTH = 300
    WINDOW_HEIGHT = -1
    
    # The window border leaves room for the triangle
    # that points up to the notification panel
    WINDOW_BORDER = 10

    def __init__(self, command, widget = None):
        super(NotificationPlugin, self).__init__()
        self._command = command
        
        if widget:
            
            self._window = gtk.Window()
            self._window.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
            width= self._window.get_size()[0]
            self._window.move(gtk.gdk.screen_width() - width, 0)
            self._window.set_default_size(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            self._window.set_border_width(self.WINDOW_BORDER)
            self._window.set_decorated(False)
            
            # Set up the window so that it can be exposed
            # with a transparent background and triangle decoration
            self._window.set_app_paintable(True)
            screen = self._window.get_screen()
            rgba = screen.get_rgba_colormap()
            self._window.set_colormap(rgba)
            self._window.connect('expose-event', self._expose)
            
            # Place the widget in an event box within the window
            # (which has a different background than the transparent window)
            self._event_box = gtk.EventBox()
            self._event_box.add(widget)
            self._window.add(self._event_box)
            
            # To do: use self._event_box.modify_bg() to adjust the background
            
            # Don't show the window now
        
    # This is basically a stop-gap so that we can use the gnome settings apps
    # until such time as all the capabilities are tied to the drop-down panel
    def get_launch_command(self):
        return self._command

    @staticmethod
    def is_plugin_enabled():
        # Default to enabled unless overridden by specific class
        return True

    # To do: make the triangle position configurable
    def _expose(self, widget, event):
        # Make the window background transparent
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.rectangle(0.0, 0.0, *widget.get_size())
        cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER)
        
        # Decorate the border with a triangle pointing up
        # Use the same color as the default event box background
        cr.set_source_rgba(0xf2/255.0, 0xf1/255.0, 0xf0/255.0, 1.0)
        cr.move_to(258, 0)
        cr.line_to(268, 10)
        cr.line_to(248, 10)
        cr.fill()
        
    def show_window(self, x, y):
        self._window.move(x, y)
        self._window.show_all()

    def hide_window(self):
        self._window.hide_all()
