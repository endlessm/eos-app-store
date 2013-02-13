from home_directory_file_copier import HomeDirectoryFileCopier

class FirefoxTasks():
    TARGET_DIR = ".mozilla"
    SOURCE_DIR = "/etc/eos-browser/mozilla"

    def __init__(self, file_copier=HomeDirectoryFileCopier()):
        self._file_copier = file_copier

    def execute(self):
       self._file_copier.copy(self.SOURCE_DIR, self.TARGET_DIR)

