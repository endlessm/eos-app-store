from distutils import dir_util
from osapps.home_path_provider import HomePathProvider
import os

class DefaultFileCopier():
    def __init__(self, destination_folder, home_path_provider=HomePathProvider(), copier=dir_util.copy_tree):
        self._destination_folder = destination_folder
        self._home_path_provider = home_path_provider
        self.copier = copier

    def copy_from(self, source_folder):
        self._destination_folder_path = self._home_path_provider.get_user_directory(self._destination_folder)
        self._destination_folder_path = os.path.join(self._destination_folder_path, "Endless")
        self.copier(source_folder, self._destination_folder_path)
