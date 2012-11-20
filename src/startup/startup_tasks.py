from eos_installer.update_manager import UpdateManager
from eos_installer.force_install import ForceInstall
from startup.remove_extra_directories import RemoveExtraDirectoriesTask
from eos_log import log


class StartupTasks(object):
    def __init__(self, tasks = [ForceInstall,UpdateManager,RemoveExtraDirectoriesTask]):
        self.TASK_PLUGINS = tasks 
    
    def perform_tasks(self):
        for task in self.TASK_PLUGINS:
            try:
                task().execute()
            except Exception as e:
                log.error("An error ocurred while executing " + task.__name__, e)

