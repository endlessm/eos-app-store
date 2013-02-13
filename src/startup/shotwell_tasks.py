from osapps.os_util import OsUtil
from distutils import dir_util
from osapps.home_path_provider import HomePathProvider

class ShotwellTasks():
    SOURCE_DIR = "/usr/share/endlessm-default-files/default_images"

    def __init__(self, file_copier=dir_util.copy_tree, home_path_provider=HomePathProvider(), os_util=OsUtil()):
        self._file_copier = file_copier
        self._home_path_provider = home_path_provider
        self._os_util = os_util

    def execute(self):
        self._file_copier(self.SOURCE_DIR, self._home_path_provider.get_pictures_directory())
        self._initialize_shotwell_settings()

    def _initialize_shotwell_settings(self):
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.ui", "show-welcome-dialog",
                "false"])
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.files", "auto-import",
                "true"])
