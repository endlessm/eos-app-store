from osapps.os_util import OsUtil
from osapps.app_launcher import AppLauncher

class AllSettingsModel():
    VERSION_COMMAND = "dpkg -p endless-os-desktop-widget | grep ^Version: | awk \"{print $2}\""
    UPDATE_COMMAND = "sudo /usr/bin/endless-installer.sh"
    SETTINGS_COMMAND = "sudo gnome-control-center"
    LOGOUT_COMMAND = "kill -9 -1"
    RESTART_COMMAND = "sudo shutdown -r now"
    SHUTDOWN_COMMAND = "sudo shutdown -h now"

    def __init__(self, os_util=OsUtil(), app_launcher=AppLauncher()):
        self._os_util = os_util
        self._app_launcher = app_launcher

    def get_current_version(self):
        return self._os_util.get_version()

    def update_software(self):
        self._app_launcher.launch(self.UPDATE_COMMAND)

    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)

    def logout(self):
        self._app_launcher.launch(self.LOGOUT_COMMAND)

    def restart(self):
        self._app_launcher.launch(self.RESTART_COMMAND)

    def shutdown(self):
        self._app_launcher.launch(self.SHUTDOWN_COMMAND)

