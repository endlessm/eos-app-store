import os.path

from startup.firefox_tasks import FirefoxTasks
from startup.shotwell_tasks import ShotwellTasks
from startup.beatbox_tasks import BeatboxTasks
from startup.windows_migration_tasks import WindowsMigrationTasks
from startup.remove_extra_directories_task import RemoveExtraDirectoriesTask
from startup.remove_extra_files_task import RemoveExtraFilesTask
from startup.delete_install_lock_task import DeleteInstallLockTask
from startup.delete_desktop_state_task import DeleteDesktopStateTask
from eos_log import log

class InitialTasks():
	TASK_PLUGINS = [
				DeleteInstallLockTask,
				FirefoxTasks, 
				ShotwellTasks, 
				BeatboxTasks,
                DeleteDesktopStateTask,
				WindowsMigrationTasks,
                RemoveExtraDirectoriesTask,
                RemoveExtraFilesTask
             ]
	def perform_tasks(self):
		if self._is_initial_startup():
			for task in self.TASK_PLUGINS:
				try:
					task().execute()
				except Exception as e:
					log.error("An error ocurred while executing " + task.__name__, e)

			self._create_initialized_file()

	def _is_initial_startup(self):
		return not os.path.exists(os.path.expanduser("~/.endlessm/.initialized"))

	def _create_initialized_file(self):
		preferences_folder = os.path.expanduser("~/.endlessm")
		
		if not os.path.exists(preferences_folder):
			os.makedirs(preferences_folder)
			
		open(os.path.expanduser(os.path.join(preferences_folder, ".initialized")), "w").close()
