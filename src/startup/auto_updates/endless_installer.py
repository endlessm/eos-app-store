from osapps.os_util import OsUtil

class EndlessInstaller():
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util
        
    def install_all_packages(self, package_directory):
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_pre_install.sh"])
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_install_all_packages.sh", package_directory])
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_post_install.sh"])


