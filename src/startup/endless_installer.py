from osapps.os_util import OsUtil
import os.path

class EndlessInstaller():
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util
        
    def install_all_packages(self, download_directory):
        self._os_util.execute(["sudo", "/usr/bin/endless_install_all_packages.sh"])


