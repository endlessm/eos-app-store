import shutil
import glob
import os
from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider
from distutils import dir_util

class HomeDirectoryCopier():
    def __init__(self, destination_folder_name, destination_finder=HomePathProvider.get_user_directory, copier=dir_util.copy_tree):
        self.destination_folder_name = destination_folder_name
        self.destination_finder = destination_finder
        self.copier = copier

    def copy_in(self, source_folder):
        destination_folder_path = self.destination_finder(self.destination_folder_name)
        self.copier(source_folder, destination_folder_path)

class BeatboxTasks():
    MUSIC_FOLDER_PATH = "/usr/share/endlessm/default_music"
    def __init__(self, home_directory_copier=HomeDirectoryCopier("Music"), os_util=OsUtil()):
        self._home_directory_copier = home_directory_copier
        self._os_util = os_util

    def execute(self):
        self._home_directory_copier.copy_in(self.MUSIC_FOLDER_PATH)
        self._os_util.execute(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", self.MUSIC_FOLDER_PATH])
