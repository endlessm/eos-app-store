from osapps.os_util import OsUtil
from simple_file_copier import SimpleFileCopier

class FirefoxTasks():
    TARGET_DIR = ".mozilla"
    
    def __init__(self, file_copier=SimpleFileCopier(TARGET_DIR), os_util=OsUtil()):
        self._file_copier = file_copier
        self._os_util = os_util

    def execute(self):
        self._file_copier.copy_from(self._default_config_folder_path())
    
    def _default_config_folder_path(self):
        return "/etc/endlessm/mozilla"
