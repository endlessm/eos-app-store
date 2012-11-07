from osapps.os_util import OsUtil
from default_file_copier import DefaultFileCopier

class ShotwellTasks():
    TARGET_DIR = "Pictures"
    
    def __init__(self, default_file_copier=DefaultFileCopier(TARGET_DIR), os_util=OsUtil()):
        self._default_file_copier = default_file_copier
        self._os_util = os_util

    def execute(self):
        self._default_file_copier.copy_from(self._default_images_folder_path())
        self._initialize_shotwell_settings()
    
    def _default_images_folder_path(self):
        return "/usr/share/endlessm/default_images"
    
    def _initialize_shotwell_settings(self):
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.ui", "show-welcome-dialog",
                "false"])
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.files", "auto-import",
                "true"])

