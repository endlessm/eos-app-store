import os.path

class ForceInstallChecker():
    def should_force_install(self):
        return os.path.exists(os.path.expanduser("~/.endlessm/needs_restart"))

    def install_accomplished(self):
        if self.should_force_install():
            os.unlink(os.path.expanduser("~/.endlessm/needs_restart"))
