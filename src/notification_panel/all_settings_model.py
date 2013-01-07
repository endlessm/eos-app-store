import time
from threading import Thread

from osapps.os_util import OsUtil
from osapps.app_launcher import AppLauncher
from startup.auto_updates.update_lock import UpdateLock
from ui.abstract_notifier import AbstractNotifier
from repo_chooser.repo_chooser_launcher import RepoChooserLauncher
from startup.auto_updates.update_manager import UpdateManager

class AllSettingsModel(AbstractNotifier):
    UPDATE_LOCK = "update.lock"
    UPDATE_STARTED = "update.started"

    VERSION_COMMAND = "dpkg -p endless-os-desktop-widget | grep ^Version: | awk \"{print $2}\""
    SETTINGS_COMMAND = "sudo gnome-control-center"
    LOGOUT_COMMAND = "kill -9 -1"
    RESTART_COMMAND = "sudo shutdown -r now"
    SHUTDOWN_COMMAND = "sudo shutdown -h now"
    
    def __init__(self, os_util=OsUtil(), app_launcher=AppLauncher(), repo_chooser_launcher = RepoChooserLauncher(), update_manager=UpdateManager()):
        self._os_util = os_util
        self._app_launcher = app_launcher
        self._repo_chooser_launcher = repo_chooser_launcher
        self._update_manager = update_manager
        
        self._still_watching = True
        self._update_thread = Thread(target=self._update_checker)
        self._is_locked = UpdateLock().is_locked()
        self._update_thread.setDaemon(True)
        self._update_thread.start()

    def _update_checker(self):
        while self._still_watching:
            current_lock = UpdateLock().is_locked()
            if current_lock != self._is_locked:
                self._notify(self.UPDATE_LOCK)
                self._is_locked = current_lock
            time.sleep(.1)

    def __del__(self):
        self._still_watching = False
        self._update_thread.join(.5)

    def get_current_version(self):
        version = self._os_util.get_version()
        return "EndlessOS {0}".format(version) if version else "EndlessOS"

    def update_software(self):
        self._repo_chooser_launcher.launch(self._repo_chosen_callback)

    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)

    def logout(self):
        self._app_launcher.launch(self.LOGOUT_COMMAND)

    def restart(self):
        self._app_launcher.launch(self.RESTART_COMMAND)

    def shutdown(self):
        self._app_launcher.launch(self.SHUTDOWN_COMMAND)

    def can_update(self):
        return not UpdateLock().is_locked()

    def _repo_chosen_callback(self):
        self._notify(self.UPDATE_STARTED)
        self._update_manager.update_os()
        
