import gtk
import os

from icon_plugin import IconPlugin
from osapps.app_launcher import AppLauncher
from background_chooser import BackgroundChooser

class AllSettingsPlugin(IconPlugin):
    UPDATE_COMMAND = 'sudo apt-get update; sudo apt-get upgrade -y'
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'
    ICON_NAME = 'settings.png'
    
    def __init__(self, icon_size):

        self._label_version = gtk.Label('EndlessOS ' + self._read_version())
        self._button_update = gtk.Button('Update')
        self._button_update.connect('button-press-event', self._update_software)
        self._button_settings = gtk.Button('Settings')
        self._button_settings.connect('button-press-event', self._launch_settings)
        self._button_desktop = gtk.Button('Desktop')
        self._button_desktop.connect('button-press-event', self._desktop_background)
        self._button_logout = gtk.Button('Log Out')
        self._button_logout.connect('button-press-event', self._logout)
        self._button_restart = gtk.Button('Restart')
        self._button_restart.connect('button-press-event', self._restart)
        self._button_shutdown = gtk.Button('Shut Down')
        self._button_shutdown.connect('button-press-event', self._shutdown)
        
        self._table = gtk.Table(6, 6, True)
        self._table.set_border_width(10)
        self._table.attach(self._label_version, 0, 3, 0, 1)
        self._table.attach(self._button_update, 3, 6, 0, 1)
        self._table.attach(self._button_settings, 0, 6, 2, 3)
        self._table.attach(self._button_desktop, 0, 6, 3, 4)
        self._table.attach(self._button_logout, 0, 2, 5, 6)
        self._table.attach(self._button_restart, 2, 4, 5, 6)
        self._table.attach(self._button_shutdown, 4, 6, 5, 6)
        
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0, self._table)

    def _update_software(self, widget, event):
        if self._confirm('Update EndlessOS?'):
            AppLauncher().launch(self.UPDATE_COMMAND)
        
    def _launch_settings(self, widget, event):
        AppLauncher().launch(self.SETTINGS_COMMAND)
        
    def _desktop_background(self, widget, event):
        BackgroundChooser(self.get_toplevel())
        
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
        
    def _read_version(self):
        pipe = os.popen('dpkg -l endless-installer | grep endless | awk \'{print $3}\'')
        version = pipe.readline()
        pipe.close()
        return version.strip()

    def show_window(self, x, y, pointer):
        # Re-read the version immediately prior to showing the window
        # so that we have the latest, even if there was a recent upgrade
        self._label_version.set_text('EndlessOS ' + self._read_version())
        super(AllSettingsPlugin, self).show_window(x, y, pointer)
