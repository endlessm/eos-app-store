from auto_updates.update_manager import UpdateManager
from auto_updates.force_install import ForceInstall
from startup.remove_extra_directories_task import RemoveExtraDirectoriesTask
from eos_log import log
from startup.remove_extra_files_task import RemoveExtraFilesTask


class StartupTasks(object):
    def __init__(self, tasks = [RemoveExtraDirectoriesTask,RemoveExtraFilesTask,ForceInstall,UpdateManager]):
        self.TASK_PLUGINS = tasks 
    
    def perform_tasks(self):
        for task in self.TASK_PLUGINS:
            try:
                task().execute()
            except Exception as e:
                log.error("An error ocurred while executing " + task.__name__, e)

