from osapps.browser_launcher import BrowserLauncher
from url_validator import UrlValidator

class SearchBoxModel():
    DEFAULT_URL = "www.google.com"

    def __init__(self, browser_launcher=BrowserLauncher, url_validator=UrlValidator()):
        self._browser_launcher = browser_launcher()
        self._url_validator = url_validator

    def search(self, search_string):
        if self._is_empty(search_string):
           self._browser_launcher.launch_browser(self.DEFAULT_URL)
        elif self._url_validator.validate(search_string):
           self._browser_launcher.launch_browser(search_string)
        else:
           self._browser_launcher.launch_search(search_string)

    def _is_empty(self, text):
        return not (text and len(text))

