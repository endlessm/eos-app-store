from distutils import dir_util
from osapps.home_path_provider import HomePathProvider

class DefaultFileCopier():
    def __init__(self, destination_folder_path, copier=dir_util.copy_tree):
        self._destination_folder_path = destination_folder_path
        self.copier = copier

    def copy_in(self, source_folder):
        self.copier(source_folder, self._destination_folder_path)

