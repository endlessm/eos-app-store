from osapps.app_launcher import AppLauncher

from util.feedback_manager import FeedbackManager
from metrics.time_provider import TimeProvider
from osapps.desktop_locale_datastore import DesktopLocaleDatastore
from osapps.app_datastore import AppDatastore
import sys

class EndlessDesktopModel(object):
    def __init__(self, app_desktop_datastore=DesktopLocaleDatastore(), app_datastore=AppDatastore(), app_launcher=AppLauncher(), feedback_manager=FeedbackManager(), time_provider=TimeProvider()):
        self._app_launcher = app_launcher
        self._feedback_manager = feedback_manager
        self._time_provider = time_provider
        self._app_desktop_datastore = app_desktop_datastore
        self._app_datastore = app_datastore
        
    def get_shortcuts(self):
        return self._app_desktop_datastore.get_all_shortcuts()

    def set_shortcuts(self, shortcuts):
        self._app_desktop_datastore.set_all_shortcuts(shortcuts)
    
    def execute_app(self, app_key, params):
        app = self._app_datastore.get_app_by_key(app_key)

        if app:
            self._app_launcher.launch(app.executable(), params)
        else:
            print >> sys.stderr, "could not find app: "+app_key
        
        
    def submit_feedback(self, message, bug):
        data = {"message":message, "timestamp":self._time_provider.get_current_time(), "bug":bug}
        self._feedback_manager.write_data(data)

    def launch_search(self, search_string):
        self._app_launcher.launch_browser(search_string)