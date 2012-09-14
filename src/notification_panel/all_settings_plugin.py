import gtk

from icon_plugin import IconPlugin
from osapps.app_launcher import AppLauncher
from util.transparent_window import TransparentWindow
from panel_constants import PanelConstants

class AllSettingsPlugin(IconPlugin):
    X_OFFSET = 30
    
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'
    ICON_NAME = 'settings.png'
    
    def __init__(self, icon_size):
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0)
        
        self._button_settings = gtk.Button('Settings')
        self._button_settings.connect('button-press-event', self._launch_settings)
        self._button_logout = gtk.Button('Log Out')
        self._button_logout.connect('button-press-event', self._logout)
        self._button_restart = gtk.Button('Restart')
        self._button_restart.connect('button-press-event', self._restart)
        self._button_shutdown = gtk.Button('Shut Down')
        self._button_shutdown.connect('button-press-event', self._shutdown)
        
        self._table = gtk.Table(2, 3, True)
        self._table.set_border_width(10)
        self._table.attach(self._button_settings, 0, 3, 0, 1)
        self._table.attach(self._button_logout, 0, 1, 1, 2)
        self._table.attach(self._button_restart, 1, 2, 1, 2)
        self._table.attach(self._button_shutdown, 2, 3, 1, 2)
        
        
        self.set_visible_window(False)
        self._window = TransparentWindow(self.get_parent_window())

        width = 330
        # To do: this does not properly account for the gnome shell top bar
        icon_size = self.size_request()[0]
        height = 120
        x = 1255
        y = 65
#        self._window.window.set_origin(x,y)
        # Get the x location of the center of the widget (icon), relative to the settings window
        self._window.move(x, y)
        
        self._window.set_size_request(width, height)
#        self._window.set_default_size(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self._window.set_border_width(self.WINDOW_BORDER)
        
        # Set up the window so that it can be exposed
        # with a transparent background and triangle decoration
        self._window.set_app_paintable(True)
#        screen = self._window.get_screen()
#        rgba = screen.get_rgba_colormap()
#        self._window.set_colormap(rgba)
        self._window.connect('expose-event', self._expose)
        
        # Place the widget in an event box within the window
        # (which has a different background than the transparent window)
        self._container = gtk.EventBox()
        self._container.add(self._table)
        self._window.add(self._container)
        self._is_active = False
        
    def execute(self):
#        screen = gtk.gdk.Screen()
#        monitor = screen.get_monitor_at_window(self.get_parent_window())
#        geometry = screen.get_monitor_geometry(monitor)
#        x = geometry.x + geometry.width - self.WINDOW_WIDTH + self.X_OFFSET
#        # Add some space between the notification panel and the window
#        extra_padding = 4
#        # To do: this does not properly account for the gnome shell top bar
#        icon_size = self.size_request()[0]
#        y = geometry.y + PanelConstants.get_padding() + icon_size + extra_padding
##        self._window.window.set_origin(x,y)
#        # Get the x location of the center of the widget (icon), relative to the settings window
#        self._pointer = self.translate_coordinates(self.get_toplevel(), icon_size / 2, 0)[0] - x
#        self._window.move(x, y)
        self._window.show_all()
        self._window.connect('focus-out-event', self._hide_window)
        
    # To do: make the triangle position configurable
    def _expose(self, widget, event):
        cr = widget.window.cairo_create()
        
        # Decorate the border with a triangle pointing up
        # Use the same color as the default event box background
        # To do: eliminate need for these "magic" numbers
        cr.set_source_rgba(0xf2/255.0, 0xf1/255.0, 0xf0/255.0, 1.0)
        self._pointer = 300
        cr.move_to(self._pointer, 0)
        cr.line_to(self._pointer + 10, 10)
        cr.line_to(self._pointer - 10, 10)
        cr.fill()
        
    def _launch_settings(self, widget, event):
        AppLauncher().launch(self.SETTINGS_COMMAND)
        
    def _logout(self, widget, event):
        if self._confirm('Log out?'):
            AppLauncher().launch(self.LOGOUT_COMMAND)
        
    def _restart(self, widget, event):
        if self._confirm('Restart?'):
            AppLauncher().launch(self.RESTART_COMMAND)
        
    def _shutdown(self, widget, event):
        if self._confirm('Shut down?'):
            AppLauncher().launch(self.SHUTDOWN_COMMAND)
        
    def _confirm(self, message):
        dialog = gtk.Dialog()
        dialog.set_decorated(False)
        dialog.set_border_width(10)
        dialog.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO)
        label = gtk.Label(message)
        label.show()
        dialog.vbox.pack_start(label)
        answer = dialog.run()
        dialog.destroy()
        return (answer == gtk.RESPONSE_YES)

    def _hide_window(self, widget, event=None):
        if (not self._window.get_visible() or self._is_active):
            self._window.hide_all()
            self._is_active = False
        else: 
            self._is_active = self._window.get_visible()

        