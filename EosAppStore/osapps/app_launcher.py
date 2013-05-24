from os_util import OsUtil
from xdg.DesktopEntry import DesktopEntry
from EosAppStore.eos_util.locale_util import LocaleUtil
from xlib_helper import XlibHelper
import os

class AppLauncher(object):
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util

    def launch(self, executable, params=[]):
        executable = [executable]
        if params:
            executable = executable + params
        self._os_util.execute_async(executable)

    def launch_file(self, filename):
        self._os_util.execute_async(["xdg-open", filename])

    def launch_desktop(self, app_name, params):
        execution = ""
        for param in self._get_desktop_entry(app_name).split(" "):
            if not param.startswith('%'):
                execution += param + " "

        self.launch(execution.strip(), params)

    def _get_desktop_entry(self, app_name):
        if app_name == "browser":
            return "x-www-browser"
        entry = DesktopEntry()
        entry.parse(os.path.join("/usr/share/endlessm-app-store/", app_name))
        return entry.getExec()
