import gtk

from icon_plugin import IconPlugin

class AllSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    ICON_NAME = 'settings.png'
    
    def __init__(self, icon_size):
        
        self._button_settings = gtk.Button('Settings')
        self._button_logout = gtk.Button('Log Out')
        self._button_restart = gtk.Button('Restart')
        self._button_shutdown = gtk.Button('Shut Down')
        
        self._table = gtk.Table(3, 2)
        self._table.set_border_width(10)
        self._table.attach(self._button_settings, 0, 3, 0, 1)
        self._table.attach(self._button_logout, 0, 1, 1, 2)
        self._table.attach(self._button_restart, 1, 2, 1, 2)
        self._table.attach(self._button_shutdown, 2, 3, 1, 2)
        
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0, self._table)
        
    
