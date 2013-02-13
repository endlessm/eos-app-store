from osapps.os_util import OsUtil
from home_directory_file_copier import HomeDirectoryFileCopier

class ShotwellTasks():
    SOURCE_DIR = "/usr/share/endlessm-default-files/default_images"
    TARGET_DIR = "Pictures"
    
    def __init__(self, home_directory_file_copier=HomeDirectoryFileCopier(), os_util=OsUtil()):
        self._home_directory_file_copier = home_directory_file_copier
        self._os_util = os_util

    def execute(self):
        self._home_directory_file_copier.copy(self.SOURCE_DIR, self.TARGET_DIR)
        self._initialize_shotwell_settings()
    
    def _initialize_shotwell_settings(self):
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.ui", "show-welcome-dialog",
                "false"])
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.files", "auto-import",
                "true"])
