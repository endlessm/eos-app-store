from distutils import dir_util
from osapps.home_path_provider import HomePathProvider
import os

class HomeDirectoryFileCopier():
    def __init__(self, home_path_provider=HomePathProvider(), copier=dir_util.copy_tree):
        self._copier = copier
        self._home_path_provider = home_path_provider

    def copy(self, source_folder, destination_folder):
        destination_home_folder = self._home_path_provider.get_user_directory(destination_folder)
        self._copier(source_folder, destination_home_folder)
