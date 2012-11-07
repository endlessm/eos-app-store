import shutil
import glob
import os
from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider

class BeatboxTasks():
    def __init__(self, default_music_directory="/usr/share/endlesm/default_music/*", home_path_provider=HomePathProvider(), os_util=OsUtil()):
        self._home_path_provider = home_path_provider
        self._os_util = os_util
        self._default_music_directory = default_music_directory

    def execute(self):
        music_folder_path = self._home_path_provider.get_user_directory("Music")
        self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", music_folder_path])
        os_util.copytree(self._default_music_directory, music_folder)
