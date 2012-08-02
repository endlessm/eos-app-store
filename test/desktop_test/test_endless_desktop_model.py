import unittest
from desktop.endless_desktop_model import EndlessDesktopModel
from mock import Mock
from osapps.app_launcher import AppLauncher
from osapps.app import App
from desktop_locale_datastore import DesktopLocaleDatastore
from app_datastore import AppDatastore
from launchable_app import LaunchableApp

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
        self.mock_desktop_locale_datastore = Mock(DesktopLocaleDatastore)
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=self.available_apps)
        self.mock_app_datastore = Mock(AppDatastore)
        self.app_mock = Mock(LaunchableApp)
        self.app_mock.executable = Mock(return_value="eog")
        self.mock_app_datastore.get_app_by_key = Mock(return_value=self.app_mock)
        self.mock_app_launcher = Mock(AppLauncher)
        
        self.testObject = EndlessDesktopModel(self.mock_desktop_locale_datastore, self.mock_app_datastore, self.mock_app_launcher)
    
    def test_initially_shortcut_list_is_retrieved_from_app_util_manager(self):
        self.assertEqual(self.available_apps, self.testObject.get_shortcuts())

    def test_execute_app_with_id_calls_launc_app_on_app_util(self):
        params = []
        self.testObject.execute_app('123', params)
        
        self.mock_app_launcher.launch.assert_called_once_with("eog", params)
        
    def test_execute_app_with_cannot_find_app_no_exception(self):
        self.mock_app_datastore = Mock(AppDatastore)
        self.mock_app_datastore.get_app_by_key = Mock(return_value=None)
        self.testObject = EndlessDesktopModel(self.mock_desktop_locale_datastore, self.mock_app_datastore, self.mock_app_launcher)
        
        params = []
        self.testObject.execute_app('123', params)
        
        self.assertFalse(self.mock_app_launcher.launch.called)
        
    def test_launch_search_launches_browser_with_search_string(self):
        search_string = "foo"
        
        self.testObject.launch_search(search_string)
        
        self.mock_app_launcher.launch_browser.assert_called_once_with(search_string)

