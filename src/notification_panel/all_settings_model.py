import os
from osapps.os_util import OsUtil
from osapps.app_launcher import AppLauncher

class AllSettingsModel():
    
    UPDATE_COMMAND = 'sudo update-manager'
    SETTINGS_COMMAND = 'sudo gnome-control-center --class=eos-network-manager'
    LOGOUT_COMMAND = 'kill -9 -1'
    RESTART_COMMAND = 'sudo shutdown -r now'
    SHUTDOWN_COMMAND = 'sudo shutdown -h now'

    DEFAULT_VERSION_FILE = "/usr/share/endlessm/version.txt"

    def __init__(self, os_util=OsUtil(), version_file=DEFAULT_VERSION_FILE, app_launcher=AppLauncher()):
        self._version_file = version_file
        self._os_util = os_util
        self._app_launcher = app_launcher

    def get_current_version(self):
        if os.path.exists(self._version_file):
            with open(self._version_file, "r") as f:
                version_text = f.read()
        else:
            try:
                version_text = "EndlessOS " + self._os_util.get_version() 
            except:
                version_text = "EndlessOS"

        return version_text

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

