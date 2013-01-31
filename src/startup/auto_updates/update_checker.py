import os

from startup.auto_updates.latest_version_provider import LatestVersionProvider
from startup.auto_updates.endless_updater import EndlessUpdater
from osapps.os_util import OsUtil

from eos_log import log

class UpdateChecker():
    def __init__(self, latest_version_provider=LatestVersionProvider(), os_util=OsUtil(), endless_updater=EndlessUpdater()):
        self._latest_version_provider = latest_version_provider
        self._os_util = os_util
        self._endless_updater = endless_updater
    
    def check_for_updates(self):
        log.info("Checking remote server for need to update")
        if self._needs_update():
            log.print_stack("Update requested")
            self._endless_updater.update()
        else:
            log.info("Current version is up to date -- no need to update")
            
    def _needs_update(self):
        remote_version = self._latest_version_provider.get_latest_version()
        local_version = self._os_util.get_version()
        
        log.info("Local version: %s -- remote version: %s" % (local_version, remote_version))
        return os.system("dpkg --compare-versions %s lt %s" % (local_version, remote_version)) == 0