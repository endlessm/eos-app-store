from startup.auto_updates.force_install_checker import ForceInstallChecker
from startup.auto_updates.endless_installer import EndlessInstaller
from startup.auto_updates.force_install_ui import ForceInstallUI
from startup.auto_updates.endless_downloader import EndlessDownloader
from threading import Thread

class ForceInstall():
    def __init__(self, force_install_checker=ForceInstallChecker(), endless_installer=EndlessInstaller(), force_install_ui=ForceInstallUI()):
        self._force_install_checker = force_install_checker
        self._endless_installer = endless_installer
        self._force_install_ui = force_install_ui

    def execute(self):
        if self._force_install_checker.should_force_install():
            self.install_in_background()

    def install_in_background(self):
        self._thread = Thread(target=self._endless_installer.install_all_packages, 
                            args=[EndlessDownloader.DEFAULT_DOWNLOAD_DIRECTORY])
        self._thread.start()

        self._force_install_ui.launch_ui()

