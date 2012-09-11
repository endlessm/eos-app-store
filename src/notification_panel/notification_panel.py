import gtk
import gobject

from osapps import app_util

from osapps.app_launcher import AppLauncher

from network_plugin import NetworkSettingsPlugin
from time_display_plugin import TimeDisplayPlugin
from bluetooth_plugin import BluetoothSettingsPlugin
from printer_plugin import PrinterSettingsPlugin
from all_settings_plugin import AllSettingsPlugin
from audio_plugin import AudioSettingsPlugin

class NotificationPanel(gtk.HBox):
    ICON_SIZE = 20
    
    # Add plugins for notification panel here
    PLUGINS = [ PrinterSettingsPlugin,
                AudioSettingsPlugin,
                BluetoothSettingsPlugin,
                NetworkSettingsPlugin,
                TimeDisplayPlugin,
                AllSettingsPlugin
              ]
    
    def __init__(self):
        super(NotificationPanel, self).__init__(False, 2)
        
        self.notification_panel = gtk.Alignment(0.5, 0.5, 0, 0)
        self.notification_panel.set_padding(20, 0, 20, 0)
        
        notification_panel_items = gtk.HBox(False)
        self.notification_panel.add(notification_panel_items)

        #Other plugins                    
        for clazz in self.PLUGINS:
            if clazz.is_plugin_enabled():
                plugin = self._register_plugin(notification_panel_items, clazz)
                plugin.connect('button-press-event', lambda w, e: self._launch_command(w.get_launch_command()))
            
        self.pack_end(self.notification_panel, False, False, 30) 

    def _register_plugin(self, notification_panel_items, clazz):
        plugin = clazz(self.ICON_SIZE)
        notification_panel_items.pack_start(plugin, False, False, 2)
        return plugin

    def _launch_command(self, command):
        if command:
            AppLauncher().launch(command)
