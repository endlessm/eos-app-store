from osapps.app_launcher import AppLauncher

class SearchBoxPresenter(object):
    DEFAULT_URL = "www.google.com"

    def __init__(self, app_launcher=AppLauncher()):
        self._app_launcher = app_launcher

    def launch_search(self, search_string):
        if search_string is None or len(search_string) == 0:
           self._app_launcher.launch_browser(self.DEFAULT_URL)
        else:
            self._app_launcher.launch_search(search_string)
