import os.path

from startup.shotwell_tasks import ShotwellTasks
from startup.beatbox_tasks import BeatboxTasks

class Tasks():
	TASK_PLUGINS = [
				ShotwellTasks, 
				BeatboxTasks,
				]
	
	def perform_startup_tasks(self):
		if self._is_initial_startup():
			for task in self.TASK_PLUGINS:
				task().execute()

			self._create_initialized_file()

	def _is_initial_startup(self):
		return not os.path.exists(os.path.expanduser("~/.endlessm/.initialized"))

	def _create_initialized_file(self):
		preferences_folder = os.path.expanduser("~/.endlessm")
		
		if not os.path.exists(preferences_folder):
			os.makedirs(preferences_folder)
			
		open(os.path.expanduser(os.path.join(preferences_folder, ".initialized")), "w").close()