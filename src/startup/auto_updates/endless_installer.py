from osapps.os_util import OsUtil
from eos_log import log

from startup.auto_updates import endpoint_provider
from startup.auto_updates.force_install_checker import ForceInstallChecker
from startup.auto_updates.endless_downloader import EndlessDownloader

class EndlessInstaller():
    def __init__(self, os_util=OsUtil(), force_install_checker=ForceInstallChecker()):
        self._os_util = os_util
        self._force_install_checker = force_install_checker
        
    def install_all_packages(self):
        try:
            log.info("executing pre install script")
            self._os_util.execute(
                                ["sudo", "/usr/bin/endless_pre_install.sh"])

            package_directory = EndlessDownloader.DEFAULT_DOWNLOAD_DIRECTORY
            log.info("executing install -- dpkg on directory %s" % package_directory)
            output = self._os_util.execute(
                                ["sudo", "/usr/bin/endless_install_all_packages.sh", package_directory])
            log.info("install output: %s" % output)

            log.info("executing post install script")
            self._os_util.execute(
                                ["sudo", "/usr/bin/endless_post_install.sh"])

            log.info("resetting the mirror endpoint to production")
            endpoint_provider.reset_url()

            log.info("turn off force install on restart")
            self._force_install_checker.install_accomplished()

            log.info("installation successful -- restarting")
            self._os_util.execute(
                                ["sudo", "/sbin/shutdown", "-r", "now"])
        except Exception as e:
            log.error("Error occurred during install", e)

