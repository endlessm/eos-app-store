import unittest
from desktop.endless_desktop_model import EndlessDesktopModel
from mock import Mock
from osapps.app_util import AppUtil
from osapps.app_launcher import AppLauncher
from osapps.app import App

class DesktopModelTestCase(unittest.TestCase):
    def setUp(self):
        self.available_apps = [
                               App(123, "app 1", "", "", "", False, False, True), 
                               App(234, "app 2", "", "", "", False, False, True), 
                               App(345, "app 3", "", "", "", False, False, True), 
                               App(456, "app 4", "", "", "", False, False, False), 
                               App(567, "app 5", "", "", "", False, False, True), 
                               App(890, "app 6", "", "", "", False, False, True), 
                               ]
        self.mock_app_util = Mock(AppUtil)
        self.mock_app_util.get_apps = Mock(return_value=self.available_apps)
        self.mock_app_launcher = Mock(AppLauncher)
        
        self.testObject = EndlessDesktopModel(self.mock_app_util, self.mock_app_launcher)
    
    def test_initially_shortcut_list_is_retrieved_from_app_util_manager(self):
        self.assertEqual(self.available_apps, self.testObject.get_shortcuts())

    def test_execute_app_with_id_calls_launc_app_on_app_util(self):
        self.testObject.execute_app_with_id('123')
        
        self.mock_app_util.launch_app.assert_called_once_with(123)
        
    def test_launch_search_launches_browser_with_search_string(self):
        search_string = "foo"
        
        self.testObject.launch_search(search_string)
        
        self.mock_app_launcher.launch_browser.assert_called_once_with(search_string)

