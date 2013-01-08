import os
import shutil
from eos_log import log 
from startup.auto_updates.force_install import ForceInstall

class DeleteInstallLockTask(object):
    def __init__(self, os_util=os, sh_util=shutil):
        self._os_util = os_util
        self._sh_util = sh_util
        
    def execute(self):
        try:
            self._os_util.remove(ForceInstall.UPGRADE_LOCK)
        except:
            log.error("Could not delete " + ForceInstall.UPGRADE_LOCK)




