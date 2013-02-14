import shutil
from osapps.home_path_provider import HomePathProvider

class GimpTasks():
    SOURCE = '/etc/endless-photo-editor/sessionrc'
    TARGET = '.gimp-2.8/sessionrc'

    def __init__(self, copier=shutil.copy, home_path_provider=HomePathProvider()):
        self._copier = copier
        self._home_path_provider = home_path_provider

    def execute(self):
        self._copier(self.SOURCE, self._home_path_provider.get_user_directory(self.TARGET))
