import shutil
from distutils import dir_util
from osapps.home_path_provider import HomePathProvider

class GimpTasks():
    SOURCE = '/etc/endless-photo-editor/sessionrc'
    TARGET_DIR = '.gimp-2.8'
    TARGET = '.gimp-2.8/sessionrc'

    def __init__(self, copier=shutil.copy, directory_creator=dir_util.mkpath, home_path_provider=HomePathProvider()):
        self._copier = copier
        self._home_path_provider = home_path_provider
        self._directory_creator = directory_creator

    def execute(self):
        destination_file = self._home_path_provider.get_user_directory(self.TARGET)
        destination_directory = self._home_path_provider.get_user_directory(self.TARGET_DIR)
        self._directory_creator(destination_directory)
        self._copier(self.SOURCE, destination_file)
