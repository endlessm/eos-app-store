from notification_plugin import NotificationPlugin
from network_manager import NetworkManager
from network_plugin_view import NetworkPluginView
from network_plugin_presenter import NetworkPluginPresenter

class NetworkSettingsPlugin(NotificationPlugin):
    COMMAND = 'sudo gnome-control-center network'

    def __init__(self, icon_size):
        super(NetworkSettingsPlugin, self).__init__(self.COMMAND)
        self._create_mvp()

    def _create_mvp(self):
        self._presenter = NetworkPluginPresenter(NetworkPluginView(self, icon_size), NetworkManager.from_dbus())

