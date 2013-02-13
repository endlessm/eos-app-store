from distutils import dir_util
from osapps.home_path_provider import HomePathProvider

class FirefoxTasks():
    TARGET_DIR = ".mozilla"
    SOURCE_DIR = "/etc/eos-browser/mozilla"

    def __init__(self, file_copier=dir_util.copy_tree, home_path_provider=HomePathProvider()):
        self._file_copier = file_copier
        self._home_path_provider = home_path_provider

    def execute(self):
       self._file_copier(self.SOURCE_DIR, self._home_path_provider.get_user_directory(self.TARGET_DIR))

