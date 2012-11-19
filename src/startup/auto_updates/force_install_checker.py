import os.path

class ForceInstallChecker():
    _RESTART_FILE = os.path.expanduser("~/.endlessm/needs_restart")

    def should_force_install(self):
        return os.path.exists(self._RESTART_FILE)

    def install_accomplished(self):
        if self.should_force_install():
            os.unlink(self._RESTART_FILE)

    def need_to_do_install(self):
        open(self._RESTART_FILE, "w").close()
