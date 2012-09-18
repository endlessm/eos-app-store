import gtk
import os

from icon_plugin import IconPlugin
from osapps.app_launcher import AppLauncher
from util.transparent_window import TransparentWindow
from util import screen_util

class AllSettingsPlugin(IconPlugin):
    UPDATE_COMMAND = 'update-manager'
    X_OFFSET = 13
    Y_LOCATION = 37
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'
    ICON_NAME = 'settings.png'
    WINDOW_WIDTH = 330
    WINDOW_HEIGHT = 160
    WINDOW_BORDER = 10
    
    def __init__(self, icon_size):
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0)
        
        self._label_version = gtk.Label('EndlessOS ' + self._read_version())
        self._button_update = gtk.Button('Update')
        self._button_update.connect('button-press-event', self._update_software)

        self._button_settings = gtk.Button('Settings')
        self._button_settings.connect('button-press-event', self._launch_settings)
        self._button_logout = gtk.Button('Log Out')
        self._button_logout.connect('button-press-event', self._logout)
        self._button_restart = gtk.Button('Restart')
        self._button_restart.connect('button-press-event', self._restart)
        self._button_shutdown = gtk.Button('Shut Down')
        self._button_shutdown.connect('button-press-event', self._shutdown)
        
        self._table = gtk.Table(4, 3, True)
        self._table.set_border_width(10)
        self._table.attach(self._label_version, 0, 3, 0, 1)
        self._table.attach(self._button_update, 0, 3, 1, 2)
        self._table.attach(self._button_settings, 0, 3, 2, 3)
        self._table.attach(self._button_logout, 0, 1, 3, 4)
        self._table.attach(self._button_restart, 1, 2, 3, 4)
        self._table.attach(self._button_shutdown, 2, 3, 3, 4)
        
        self.set_visible_window(False)
        self._window = TransparentWindow(self.get_parent_window())

        icon_size = self.size_request()[0]
        x = screen_util.get_width() - self.WINDOW_WIDTH - self.X_OFFSET
    
        # Get the x location of the center of the widget (icon), relative to the settings window
        self._window.move(x, self.Y_LOCATION)
        
        self._window.set_size_request(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self._window.set_border_width(self.WINDOW_BORDER)
        
        # Set up the window so that it can be exposed
        # with a transparent background and triangle decoration
        self._window.connect('expose-event', self._expose)
        
        # Place the widget in an event box within the window
        # (which has a different background than the transparent window)
        self._container = gtk.EventBox()
        self._container.add(self._table)
        self._window.add(self._container)
        self._is_active = False
        
    def execute(self):
        self._window.show_all()
        self._window.connect('focus-out-event', self._hide_window)

    # To do: make the triangle position configurable
    def _expose(self, widget, event):
#        self._update_version_text()

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

    def _read_version(self):
        pipe = os.popen('dpkg -l endless-installer* | grep endless | awk \'{print $3}\'')
        version = pipe.readline()
        pipe.close()
        return version.strip()

    def _update_software(self, widget, event):
        if self._confirm('Update EndlessOS?'):
            AppLauncher().launch(self.UPDATE_COMMAND)

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
