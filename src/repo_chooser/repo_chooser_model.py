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
        if hasattr(self, "_chosen_repo"):
            return self._chosen_repo.display_name
        return ""

    def choose_repository(self, password):
        self._chosen_repo = self._environment_manager.find_repo(password)
        self._notify(self.REPO_CHANGED)

    def do_update(self):
        if hasattr(self, "_chosen_repo"):
            endpoint_provider.set_endless_url(self._chosen_repo.repo_url)

        self._update_manager.update_os()
