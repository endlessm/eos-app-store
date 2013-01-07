import os
import shutil
from eos_log import log 

class DeleteDesktopStateTask:
    def __init__(self, os_util=os, sh_util=shutil):
        self._os_util = os_util
        self._sh_util = sh_util
        
    def execute(self):
        
        self._sh_util.copyfile("/etc/endlessm/installed_applications.json", "~/.endlessm/installed_applications.json")
        
        try:
            self._os_util.remove(os.path.expanduser("~/.endlessm/desktop.json"))
        except:
            log.error("Could not delete ~/.endlessm/desktop.json")


