from osapps.os_util import OsUtil
from eos_log import log

class EndlessInstaller():
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util
        
    def install_all_packages(self, package_directory):
        log.info("executing pre install script")
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_pre_install.sh"])

        log.info("executing install -- dpkg")
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_install_all_packages.sh", package_directory])

        log.info("executing post install script")
        self._os_util.execute(
                            ["sudo", "/usr/bin/endless_post_install.sh"])


