from startup.auto_updates.update_manager import UpdateManager
from startup.auto_updates.force_install import ForceInstall
from startup.remove_extra_directories import RemoveExtraDirectoriesTask
from eos_log import log


class StartupTasks(object):
    DEFAULT_TASKS = [ForceInstall,UpdateManager,RemoveExtraDirectoriesTask]
    def __init__(self, tasks = DEFAULT_TASKS):
        self._all_tasks = tasks 
    
    def perform_tasks(self):
        for task in self._all_tasks:
            try:
                task().execute()
            except Exception as e:
                log.error("An error ocurred while executing " + task.__name__, e)

