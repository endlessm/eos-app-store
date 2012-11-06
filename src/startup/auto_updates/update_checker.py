import re
from startup.auto_updates.latest_version_provider import LatestVersionProvider
from startup.auto_updates.endless_updater import EndlessUpdater
from osapps.os_util import OsUtil

class UpdateChecker():
    def __init__(self, latest_version_provider=LatestVersionProvider(), os_util=OsUtil(), endless_updater=EndlessUpdater()):
        self._latest_version_provider = latest_version_provider
        self._os_util = os_util
        self._endless_updater = endless_updater
    
    def check_for_updates(self):
        if self._needs_update():
            self._endless_updater.update()
            
    def _needs_update(self):
        remote_version = self._latest_version_provider.get_latest_version()
        local_version = self._os_util.get_version()
        
        return cmp(self._normalize(remote_version), self._normalize(local_version)) > 0

    def _normalize(self, v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]