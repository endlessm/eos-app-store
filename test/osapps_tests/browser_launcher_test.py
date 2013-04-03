from mock import Mock
from unittest import TestCase
from osapps.browser_launcher import BrowserLauncher

class BrowserLauncherTest(TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._mock_xlib_helper = Mock()
        self._test_object = BrowserLauncher(self._mock_os_util, Mock(return_value=self._mock_xlib_helper))
    
    def test_launch_browser_opens_existing_instance_when_available(self):
        self._mock_xlib_helper.bring_app_to_front = Mock(return_value=True)

        self._test_object.launch_browser()

        assert not self._mock_os_util.execute_async.called 
        
    def test_launch_browser_opens_new_instance_when_one_does_not_exist(self):
        self._mock_xlib_helper.bring_app_to_front = Mock(return_value=False)

        self._test_object.launch_browser()

        self._mock_os_util.execute_async.assert_called_once_with(["x-www-browser"]) 

    def test_launch_browser_with_url_works(self):
        url = "foo"
        
        self._test_object.launch_browser(url)
        
        self._mock_os_util.execute_async.assert_called_once_with(["x-www-browser", "-new-tab", "\"\"\"" + url + "\"\"\""])
        
    def test_launch_browser_without_url_works(self):
        self._mock_xlib_helper.bring_app_to_front = Mock(return_value=False)
        self._test_object.launch_browser()
        
        self._mock_os_util.execute_async.assert_called_once_with(["x-www-browser"])
        
    def test_launch_search_with_search_string_works(self):
        search_string = "foo"
        search_prefix = "www.google.com/search?q="
        
        self._test_object.launch_search(search_string)
        
        self._mock_os_util.execute_async.assert_called_once_with(["x-www-browser", "-new-tab", "\"\"\"" + search_prefix + search_string + "\"\"\""])
        
