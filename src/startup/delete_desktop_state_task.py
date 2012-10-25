import shutil
import os.path

class DeleteDesktopStateTask:
    def __init__(self, shell_util=shutil):
        self._shell_utils = shell_util
        
    def execute(self):
        self._shell_utils.rmtree(os.path.expanduser("~/.endlessm/desktop.json"), True)
