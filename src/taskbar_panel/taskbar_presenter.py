class TaskbarPresenter(object):
    def __init__(self, app_launcher):
        pass
        self._app_launcher = app_launcher


    def launch_search(self, search_string):
        self._app_launcher.launch_browser(search_string)

