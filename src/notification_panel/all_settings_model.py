import os
from osapps.os_util import OsUtil
from osapps.app_launcher import AppLauncher
from endpoint_provider import EndpointProvider

class AllSettingsModel():
    
    UPDATE_COMMAND = 'sudo update-manager'
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'

    def __init__(self, os_util=OsUtil(), endpoint_provider=EndpointProvider(), app_launcher=AppLauncher()):
        self._endpoint_provider = endpoint_provider
        self._os_util = os_util
        self._app_launcher = app_launcher

    def get_current_version(self):
        return self._os_util.get_version()

    def update_software(self):
        self._app_launcher.launch(
                          self.UPDATE_COMMAND.format(
                                             self._endpoint_provider.get_server_endpoint()))

    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)

    def logout(self):
        self._app_launcher.launch(self.LOGOUT_COMMAND)

    def restart(self):
        self._app_launcher.launch(self.RESTART_COMMAND)

    def shutdown(self):
        self._app_launcher.launch(self.SHUTDOWN_COMMAND)

