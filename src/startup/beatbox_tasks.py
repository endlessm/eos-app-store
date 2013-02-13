from home_directory_file_copier import HomeDirectoryFileCopier
from osapps.home_path_provider import HomePathProvider
from osapps.os_util import OsUtil

class BeatboxTasks():
    SOURCE_DIR = "/usr/share/endlessm-default-files/default_music"
    TARGET_DIR = "Music/Endless"

    def __init__(self, home_directory_file_copier=HomeDirectoryFileCopier(), home_path_provider=HomePathProvider(), os_util=OsUtil()):
        self._home_directory_file_copier = home_directory_file_copier
        self._home_path_provider = home_path_provider
        self._os_util = os_util

    def execute(self):
        self._home_directory_file_copier.copy(self.SOURCE_DIR, self.TARGET_DIR)
        self._initialize_beatbox_settings()

    def _initialize_beatbox_settings(self):
        return self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.Settings", 
                "music-folder", self._home_path_provider.get_user_directory()])
