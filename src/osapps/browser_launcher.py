from os_util import OsUtil
from xlib_helper import XlibHelper

class BrowserLauncher():
    def __init__(self, os_util=OsUtil(), xlib_helper=XlibHelper):
        self._xlib_helper = xlib_helper()
        self._os_util = os_util

    def launch_browser(self, url=None):
        if url or not self._xlib_helper.bring_app_to_front("firefox"):
            self._os_util.execute_async(self._scrub_params(url))

    def launch_search(self, search_string):
        # Command-line argument for search in Firefox
        search_prefix = "www.google.com/search?q="
        search = search_prefix + search_string
        self._os_util.execute_async(self._scrub_params(search))

    def _scrub_params(self, url):
        params = ["x-www-browser"]
        if url:
            params.append("-new-tab")
            params.append("\"\"\"" + url + "\"\"\"")
        return params
