import gtk
import gobject

from osapps import app_util

from osapps.app_launcher import AppLauncher

from network_plugin import NetworkSettingsPlugin
from time_display_plugin import TimeDisplayPlugin
from bluetooth_plugin import BluetoothSettingsPlugin
from feedback_plugin import FeedbackPlugin

class NotificationPanel(gtk.HBox):
    ICON_SIZE = 20
    
    # Add plugins for notification panel here
    PLUGINS = [ BluetoothSettingsPlugin,
                NetworkSettingsPlugin, 
                TimeDisplayPlugin 
              ]
    
    __gsignals__ = {
        "feedback-launched": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   ())
    }

        
    def __init__(self):
        super(NotificationPanel, self).__init__(False,2)
        
        self.notification_panel = gtk.Alignment(0.5, 0.5, 0, 0)
        self.notification_panel.set_padding(20, 0, 20, 0)
        
        notification_panel_items = gtk.HBox(False)
        self.notification_panel.add(notification_panel_items)

        # Feedback plugin
        plugin = self._register_plugin(notification_panel_items, FeedbackPlugin)
        plugin.connect('button-press-event', lambda w, e: self.emit("feedback-launched"))
                    
        #Other plugins                    
        for clazz in self.PLUGINS:
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
