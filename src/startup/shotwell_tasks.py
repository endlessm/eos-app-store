from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider
import shutil
import glob
import os
import os.path

class ShotwellTasks():
	def __init__(self, home_path_provider=HomePathProvider(), os_util=OsUtil()):
		self._home_path_provider = home_path_provider
		self._os_util = os_util
	
	def execute(self):
		self._initialize_shotwell_settings()
		self._copy_default_images()
	
	
	def _initialize_shotwell_settings(self):
		self._os_util.execute(["gsettings", "set", 
				"org.yorba.shotwell.preferences.ui", "show-welcome-dialog", 
				"false"])
		self._os_util.execute(["gsettings", "set", 
				"org.yorba.shotwell.preferences.files", "auto-import", 
				"true"])
	
	def _copy_default_images(self):
		pictures_directory = self._home_path_provider.get_user_directory('Pictures')
		
		# Put the default pictures in a sub-folder named 'Endless'
		pictures_directory = os.path.join(pictures_directory, 'Endless')
		
		for path in glob.iglob(self._default_images_directory()):
			shutil.copy2(path, os.path.join(pictures_directory, os.path.basename(path)))

	def _default_images_directory(self):
		return '/usr/share/endlessm/default_images/*'