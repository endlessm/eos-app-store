from startup.auto_updates.force_install_checker import ForceInstallChecker
from eos_installer.endless_installer import EndlessInstaller
from startup.auto_updates.force_install_ui import ForceInstallUI
from threading import Thread
from eos_log import log
from eos_installer import endpoint_provider
from osapps.os_util import OsUtil

class ForceInstall():
    def __init__(self, force_install_checker=ForceInstallChecker(), 
            endless_installer=EndlessInstaller(), 
            force_install_ui=ForceInstallUI(),
            os_util=OsUtil()):
        self._force_install_checker = force_install_checker
        self._endless_installer = endless_installer
        self._force_install_ui = force_install_ui
        self._os_util = os_util

    def execute(self):
        if self._force_install_checker.should_force_install():
            log.info("proceeding to force install")
            self.install_in_background()
        else:
            log.info("no need to force install")

    def install_in_background(self):
        log.info("launching installer in thread")
        self._thread = Thread(target=self._background_installation_task)
        self._thread.start()

        self._force_install_ui.launch_ui()

    def _background_installation_task(self):
        self._endless_installer.install_all_packages()

        log.info("resetting the mirror endpoint to production")
        endpoint_provider.reset_url()

        log.info("turn off force install on restart")
        self._force_install_checker.install_accomplished()

        log.info("installation successful -- restarting")
        self._os_util.execute(
                            ["sudo", "/sbin/shutdown", "-r", "now"])

