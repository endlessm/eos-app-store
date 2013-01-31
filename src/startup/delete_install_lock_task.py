import os
import shutil
from eos_log import log 
from startup.auto_updates.force_install import ForceInstall

class DeleteInstallLockTask(object):
    def __init__(self, os_util=os):
        self._os_util = os_util
        
    def execute(self):
        try:
            self._os_util.remove(ForceInstall.UPGRADE_LOCK)
        except:
            log.error("Could not delete " + ForceInstall.UPGRADE_LOCK)




