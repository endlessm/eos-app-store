import sys
from ui.abstract_notifier import AbstractNotifier
from eos_installer import endpoint_provider
from environment_manager import EnvironmentManager
from eos_installer.update_manager import UpdateManager
from eos_log import log

class RepoChooserModel(AbstractNotifier):
    REPO_CHANGED = "repo.changed"

    def __init__(self, environment_manager=EnvironmentManager(), update_manager=UpdateManager()):
        self._environment_manager = environment_manager
        self._update_manager = update_manager

    def get_chosen_repository(self):
        return self._environment_manager.get_current_repo()

    def choose_repository(self, password):
        self._environment_manager.set_current_repo(password)
        self._notify(self.REPO_CHANGED)

    def do_update(self):
        log.info("kicking off manual update")
        self._update_manager.update_os()
