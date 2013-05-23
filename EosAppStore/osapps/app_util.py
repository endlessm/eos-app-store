from app_datastore import AppDatastore
from file_app_associator import FileAppAssociator
from app_launcher import AppLauncher

from EosAppStore.eos_log import log

class AppUtil(object):
    def __init__(self, datastore=AppDatastore(), launcher=AppLauncher, 
                 file_app_associator=FileAppAssociator()):
        self._datastore = datastore
        self._launcher = launcher()
        self._file_app_associator = file_app_associator
    
    def launch_app(self, app_id):
        app_by_id = self._datastore.get_app_by_id(app_id)

        if app_by_id is not None:
            self._launcher.launch(app_by_id.executable())

    def _get_app_for_file(self, filename):
        app_name = self._file_app_associator.associated_app(filename)
        return self._datastore.find_app_by_desktop(app_name)
    
    def launch_file(self, filename):
        app = self._get_app_for_file(filename)
        if app:
            self._launcher.launch_file(filename)
        else:
            log.error("Could not open: " + filename)
