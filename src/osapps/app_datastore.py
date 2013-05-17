import sys
from app import App
import json
import copy
from desktop_filetype_util import DesktopFiletypeUtil
from launchable_app import LaunchableApp
from eos_log import log

class AppDatastore(object):
        
    def __init__(self, filename="/etc/endlessm/application.list", desktop_filetype_util = DesktopFiletypeUtil()):
        self._filename = filename
        self._desktop_filetype_util = desktop_filetype_util
        self._apps = {}
        self._get_all_apps()
        
    
    def _get_all_apps(self):
        try:
            with open(self._filename, "r") as f:
                for key, value in json.load(f).iteritems():
                    try:
                        app = self._convert_dict_to_app(value)
                        self._apps[key] = app
                    except:
                        log.error("Could not read desktop file "+ repr(sys.exc_info()))
                        continue
        except Exception as e:
            log.error("An error occurred trying to read the file: " + self._filename, e)

    def get_app_by_key(self, app_key):
        app = None
        try:
            app = self._apps[app_key]
        except:
            log.error("app isn't in list: " + repr(app_key))
            
        return app

    def _convert_dict_to_app(self, desktop):
        
        executable = None
        
        if desktop and ".desktop" in desktop:
            executable = self._desktop_filetype_util.get_executable(desktop)
        
        return LaunchableApp(executable, desktop)
    
    def find_app_by_desktop(self, desktop):
        for key, value in self._apps.iteritems():
            if str(value.desktop()) == desktop:
                return value
        return None
