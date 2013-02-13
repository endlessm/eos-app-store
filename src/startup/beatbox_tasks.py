from osapps.home_path_provider import HomePathProvider
from osapps.os_util import OsUtil
from distutils import dir_util

class BeatboxTasks():
    SOURCE_DIR = "/usr/share/endlessm-default-files/default_music"
    TARGET_DIR = "Endless"

    def __init__(self, file_copier=dir_util.copy_tree, home_path_provider=HomePathProvider(), os_util=OsUtil()):
        self._file_copier = file_copier
        self._home_path_provider = home_path_provider
        self._os_util = os_util

    def execute(self):
        self._file_copier(self.SOURCE_DIR, self._home_path_provider.get_music_directory(self.TARGET_DIR))
        self._initialize_beatbox_settings()

    def _initialize_beatbox_settings(self):
        return self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.Settings", 
                "music-folder", self._home_path_provider.get_music_directory()])
