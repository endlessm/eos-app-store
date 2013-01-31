from eos_widgets.abstract_notifier import AbstractNotifier
from startup.auto_updates.latest_version_provider import LatestVersionProvider

class InstallNotifierModel(AbstractNotifier):
    ACTION_TAKEN = "action.taken"
    
    def __init__(self, latest_version_provider=LatestVersionProvider()):
        self._latest_version_provider = latest_version_provider
    
    def should_install(self):
        return self._should_install
    
    def get_new_version(self):
        version = self._latest_version_provider.get_latest_version()
        return version[:version.index(";")]

    def install_now(self):
        self._should_install = True
        self._notify(self.ACTION_TAKEN)
    
    def install_later(self):
        self._should_install = False
        self._notify(self.ACTION_TAKEN)
