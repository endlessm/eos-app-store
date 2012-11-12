from startup.auto_updates.force_install_checker import ForceInstallChecker
from startup.auto_updates.endless_installer import EndlessInstaller

class ForceInstall():
    def __init__(self, force_install_checker=ForceInstallChecker(), endless_installer=EndlessInstaller()):
        self._force_install_checker = force_install_checker
        self._endless_installer = endless_installer

    def execute(self):
        if self._force_install_checker.should_force_install():
            self._endless_installer.install_all_packages()
