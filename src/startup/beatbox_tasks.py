from default_file_copier import DefaultFileCopier
from osapps.home_path_provider import HomePathProvider
from osapps.os_util import OsUtil

class BeatboxTasks():
    TARGET_DIR = "Music"
    
    def _default_music_folder_path(self):
        return "/usr/share/endlessm/default_music"
    
    def __init__(self, home_path=HomePathProvider.get_user_directory, default_file_copier=DefaultFileCopier(TARGET_DIR), os_util=OsUtil()):
        self._default_file_copier = default_file_copier
        self._os_util = os_util
        self._home_path = home_path(self.TARGET_DIR)

    def execute(self):
        self._default_file_copier.copy_from(self._default_music_folder_path())
        self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", self._home_path])
