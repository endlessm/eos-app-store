from osapps.os_util import OsUtil
from osapps.app_launcher import AppLauncher
from version_provider import VersionProvider

class AllSettingsModel():
    VERSION_COMMAND = "dpkg -p endless-os-desktop-widget | grep ^Version: | awk \"{print $2}\""
    UPDATE_COMMAND = 'wget -q -O- http://{0}/installer.sh > /tmp/endless-installer.sh && gksudo bash /tmp/endless-installer.sh'
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'

    def __init__(self, os_util=OsUtil(), version_provider=VersionProvider(), app_launcher=AppLauncher()):
        self._version_provider = version_provider
        self._os_util = os_util
        self._app_launcher = app_launcher

    def get_current_version(self):
        return self._version_provider.get_current_version()

    def update_software(self):
        self._app_launcher.launch(self.UPDATE_COMMAND.format(self._version_provider.get_server_endpoint()))

    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)

    def logout(self):
        self._app_launcher.launch(self.LOGOUT_COMMAND)

    def restart(self):
        self._app_launcher.launch(self.RESTART_COMMAND)

    def shutdown(self):
        self._app_launcher.launch(self.SHUTDOWN_COMMAND)

