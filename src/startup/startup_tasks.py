from auto_updates.update_manager import UpdateManager
from auto_updates.force_install import ForceInstall
from eos_log import log

class StartupTasks(object):
    TASK_PLUGINS = [
                    ForceInstall,
                    UpdateManager
                ]
    
    def perform_tasks(self):
        for task in self.TASK_PLUGINS:
            try:
                task().execute()
            except Exception as e:
                log.error("An error ocurred while executing " + task.__name__, e)

