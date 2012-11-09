import sys
from ui.abstract_notifier import AbstractNotifier
from startup.auto_updates import endpoint_provider
from environment_manager import EnvironmentManager
from startup.auto_updates.update_manager import UpdateManager

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
        self._update_manager.update_os()
