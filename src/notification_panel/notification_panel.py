import gtk

from network_plugin import NetworkSettingsPlugin
from time_display_plugin import TimeDisplayPlugin
from bluetooth_plugin import BluetoothSettingsPlugin
from printer_plugin import PrinterSettingsPlugin
from battery_plugin import BatteryPlugin
from all_settings_plugin import AllSettingsPlugin
from audio_plugin import AudioSettingsPlugin

from panel_constants import PanelConstants

from eos_log import log
from social_bar.social_bar_plugin import SocialBarPlugin

class NotificationPanel(gtk.HBox):
    # Add plugins for notification panel here
    PLUGINS = [ TimeDisplayPlugin,
                PrinterSettingsPlugin,
                BluetoothSettingsPlugin,
                BatteryPlugin,
                NetworkSettingsPlugin,
                AudioSettingsPlugin,
                SocialBarPlugin,
                AllSettingsPlugin
              ]
    def __init__(self, parent):
        super(NotificationPanel, self).__init__(False, 2)
        self._parent = parent

        self.notification_panel = gtk.Alignment(0.5, 0.5, 0, 0)
        self.notification_panel.set_padding(0, 0, 0, 3)
        self.plugins_list = []
        notification_panel_items = gtk.HBox(False)
        self.notification_panel.add(notification_panel_items)

        #Other plugins
        for clazz in self.PLUGINS:
            try:
                if clazz.is_plugin_enabled():
                    plugin = self._register_plugin(notification_panel_items, clazz)
                    
                    # At some point, it would most likely make sense to refactor this.  Currently,
                    # with each click, both the button-press and hide events are chosen, and separate logic
                    # then has to be inserted into each plugin to handle this.  A single event handler method
                    # seems to make more sense.
                    plugin.connect('button-release-event', lambda w, e: self._launch_command(w))
                    plugin.connect('hide-window-event', plugin._hide_window)
                    self.plugins_list.append(plugin)
            except Exception, e:
                log.error('Error registering plugin for ' + clazz.__name__ + ': ' + e.message)

        self.pack_end(self.notification_panel, False, False, 5)

    def _register_plugin(self, notification_panel_items, clazz):
        plugin = clazz(PanelConstants.get_icon_size())
        plugin.set_parent(self._parent)
        plugin.post_init()
        notification_panel_items.pack_start(plugin, False, False, 2)
        return plugin

    def _launch_command(self, widget):
        widget.execute()

    def close_settings_plugin_window(self):
        for plugin in self.plugins_list:
            plugin.emit("hide-window-event")

