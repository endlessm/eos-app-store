import gtk

from icon_plugin import IconPlugin
from osapps.app_launcher import AppLauncher

class AllSettingsPlugin(IconPlugin):
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'
    ICON_NAME = 'settings.png'
    
    def __init__(self, icon_size):
        
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
        
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0, self._table)
        
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
        