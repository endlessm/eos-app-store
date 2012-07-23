import gtk

from osapps import app_util

from network_plugin import NetworkSettingsPlugin
from osapps.app_launcher import AppLauncher

class NotificationPanel(gtk.HBox):
    ICON_SIZE = 24
    
    # Add plugins for notification panel here
    PLUGINS = [ NetworkSettingsPlugin ]
        
    def __init__(self):
        super(NotificationPanel, self).__init__(False,2)
        
        self.notification_panel = gtk.Alignment(0.5, 0.5, 0, 0)
        self.notification_panel.set_padding(20, 0, 20, 0)
        
        notification_panel_items = gtk.HBox(False)
        self.notification_panel.add(notification_panel_items)

        for clazz in self.PLUGINS:
            plugin = clazz(self.ICON_SIZE)
            plugin.connect('button-press-event', lambda w, e: self._launch_command(w.get_launch_command()))
            notification_panel_items.pack_start(plugin)
            
        self.pack_end(self.notification_panel, False, False, 30) 

    def _launch_command(self, command):
        AppLauncher().launch(command)
