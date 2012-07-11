from osapps.app_util import AppUtil
from osapps.app_launcher import AppLauncher

from util.feedback_manager import FeedbackManager
from metrics.time_provider import TimeProvider

class EndlessDesktopModel(object):
    def __init__(self, app_util=AppUtil(), app_launcher=AppLauncher(), feedback_manager=FeedbackManager(), time_provider=TimeProvider()):
        self._app_util = app_util
        self._app_launcher = app_launcher
        self._feedback_manager = feedback_manager
        self._installed_apps = self._app_util.installed_apps()
        self._time_provider = time_provider
        
    def get_shortcuts(self):
        return self._installed_apps
    
    def get_menus(self):
        apps = self._app_util.get_available_apps()
        return [app for app in apps if app not in self._installed_apps and app.is_visible()]
    
    def add_item(self, shortcut):
        self._app_util.save(shortcut)
        self._installed_apps = self._app_util.installed_apps()
        
    def remove_item(self, app_id):
        self._app_util.remove(app_id)
        self._installed_apps = self._app_util.installed_apps()

    def rename_item(self, shortcut, title):
        self._app_util.rename(shortcut, title)
        self._installed_apps = self._app_util.installed_apps()
    
    def reorder_shortcuts(self, app_ids):
        app_dict = {}
        for app in self._installed_apps:
            app_dict[app.id()] = app
        
        apps = [app_dict[int(app_id)] for app_id in app_ids]
            
        self._app_util.save_all(apps)
        self._installed_apps = self._app_util.installed_apps()
    
    def execute_app_with_id(self, app_id):
        self._app_util.launch_app(int(app_id))
    
    def submit_feedback(self, message, bug):
        data = {"message":message, "timestamp":self._time_provider.get_current_time(), "bug":bug}
        self._feedback_manager.write_data(data)

    def launch_search(self, search_string):
        self._app_launcher.launch_browser(search_string)