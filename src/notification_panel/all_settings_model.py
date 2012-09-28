import os
from osapps.os_util import OsUtil

class AllSettingsModel():
    VERSION_COMMAND = "dpkg -l endless-os-desktop-widget | grep endless | awk \"{print $3}\""
    DEFAULT_VERSION_FILE = "/usr/share/endlessm/version.txt"

    def __init__(self, os_util=OsUtil(), version_file=DEFAULT_VERSION_FILE):
        self._version_file = version_file
        self._os_util = os_util

    def get_current_version(self):
        if os.path.exists(self._version_file):
            with open(self._version_file, "r") as f:
                version_text = f.read()
        else:
            try:
                version_text = "EndlessOS " + self._os_util.execute(self.VERSION_COMMAND)
            except:
                version_text = "EndlessOS"

        return version_text
