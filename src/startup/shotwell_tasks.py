from osapps.os_util import OsUtil
from default_file_copier import DefaultFileCopier
from osapps.home_path_provider import HomePathProvider
class ShotwellTasks():
    TARGET_DIR = "Pictures"
    IMAGES_FOLDER_PATH = "/usr/share/endlessm/default_images"
    def __init__(self,
            home_path_provider=HomePathProvider.get_user_directory,
            default_file_copier=DefaultFileCopier(TARGET_DIR), os_util=OsUtil()):
        self._default_file_copier = default_file_copier
        self._os_util = os_util
        self._home_path = home_path_provider(self.TARGET_DIR)

    def execute(self):
        self._default_file_copier.copy_in(self.IMAGES_FOLDER_PATH)
        self._initialize_shotwell_settings()


    def _initialize_shotwell_settings(self):
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.ui", "show-welcome-dialog",
                "false"])
        self._os_util.execute(["gsettings", "set",
                "org.yorba.shotwell.preferences.files", "auto-import",
                "true"])

