import shutil
import glob
import os
from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider

class BeatboxTasks():
    def __init__(self, home_path_provider=HomePathProvider(), os_util=OsUtil()):
        self._home_path_provider = home_path_provider
        self._os_util = os_util

    def execute(self):
        music_folder = self._home_path_provider.get_user_directory("Music")

        self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", music_folder])
        for path in glob.iglob(self._default_music_directory()):
            shutil.copy2(path, os.path.join(music_folder, os.path.basename(path)))

    def _default_music_directory(self):
        return "/usr/share/endlesm/default_music"
