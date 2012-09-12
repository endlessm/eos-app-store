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
from notification_plugin import NotificationPlugin

class NotificationPanel(gtk.HBox):
    ICON_SIZE = 20
    PADDING = 20
    
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
        self.notification_panel.set_padding(self.PADDING, 0, self.PADDING, 0)
        
        notification_panel_items = gtk.HBox(False)
        self.notification_panel.add(notification_panel_items)

        #Other plugins                    
        for clazz in self.PLUGINS:
            if clazz.is_plugin_enabled():
                plugin = self._register_plugin(notification_panel_items, clazz)
                plugin.connect('button-press-event', lambda w, e: self._launch_command(w))
            
        self.pack_end(self.notification_panel, False, False, 30) 

    def _register_plugin(self, notification_panel_items, clazz):
        plugin = clazz(self.ICON_SIZE)
        notification_panel_items.pack_start(plugin, False, False, 2)
        return plugin

    def _launch_command(self, widget):
        command = widget.get_launch_command()
        if command:
            AppLauncher().launch(command)
        else:
            screen = gtk.gdk.Screen()
            monitor = screen.get_monitor_at_window(widget.get_parent_window())
            geometry = screen.get_monitor_geometry(monitor)
            width = geometry.width
            height = geometry.height
            x = geometry.x + geometry.width - NotificationPlugin.WINDOW_WIDTH
            # Add some space between the notification panel and the window
            extra_padding = 4
            y = geometry.y + self.PADDING + self.ICON_SIZE + extra_padding
            widget.show_window(x, y)
