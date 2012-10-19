from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider

import shutil
import os.path

class Tasks():
	def __init__(self, home_path_provider=HomePathProvider()):
		self._home_path_provider = home_path_provider

	def perform_startup_tasks(self, os_util=OsUtil()):
		if self._is_initial_startup():
			self.initialize_shotwell_settings(os_util)
			self.copy_default_images()

			self._create_initialized_file()

	def initialize_shotwell_settings(self, os_util):
		os_util.execute(["gsettings", "set", 
				"org.yorba.shotwell.preferences.ui", "show-welcome-dialog", 
				"false"])
		os_util.execute(["gsettings", "set", 
				"org.yorba.shotwell.preferences.files", "auto-import", 
				"true"])

	def copy_default_images(self):
		pictures_directory = self._home_path_provider.get_user_directory("Pictures")
		shutil.copytree("/usr/share/endlessm/default_images", pictures_directory)

	def _is_initial_startup(self):
		return not os.path.exists(os.path.expanduser("~/.endlessm/.initialized"))

	def _create_initialized_file(self):
		open(os.path.expanduser("~/.endlessm/.initialized"), "w").close()
