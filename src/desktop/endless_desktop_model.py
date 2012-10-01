from osapps.app_launcher import AppLauncher

from util.feedback_manager import FeedbackManager
from metrics.time_provider import TimeProvider
from osapps.desktop_locale_datastore import DesktopLocaleDatastore
from osapps.app_datastore import AppDatastore
import sys
from util import image_util
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore

class EndlessDesktopModel(object):
    def __init__(self, app_desktop_datastore=DesktopLocaleDatastore(), app_datastore=AppDatastore(), app_launcher=AppLauncher(), feedback_manager=FeedbackManager(), time_provider=TimeProvider(), preferences_provider=DesktopPreferencesDatastore()):
        self._app_launcher = app_launcher
        self._feedback_manager = feedback_manager
        self._time_provider = time_provider
        self._app_desktop_datastore = app_desktop_datastore
        self._app_datastore = app_datastore
        self._preferences_provider = preferences_provider
        print "Preferences in MODEL: ", self._preferences_provider
    def get_shortcuts(self):
        return self._app_desktop_datastore.get_all_shortcuts()
    
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
        
    def set_background(self, filename):
        new_image_path = image_util.image_path(filename)
        self._preferences_provider.set_background(new_image_path)
        
    def get_background(self):
        return self._preferences_provider.get_background()

    def get_default_background(self):
        return self._preferences_provider.get_default_background()
    
    def get_preferences(self):
        return self._preferences_provider

