from unittest import TestCase
from osapps.app_util import AppUtil
from mock import Mock
from osapps.app import App

class AppUtilTest(TestCase):
    def setUp(self):
        self._mock_app_datastore = Mock()
        self._mock_app_launcher = Mock()
        self._mock_file_app_associator = Mock()
        self._test_object = AppUtil(self._mock_app_datastore, 
                                    Mock(return_value=self._mock_app_launcher),
                                    self._mock_file_app_associator)
            
    def test_launch_app_should_call_launcher_with_executable_from_given_app_id(self):
        app1 = App(1, "App one", "app1.desktop", "exec_one", "icon_one")
        app2 = App(2, "App two", "app2.desktop", "exec_two", "icon_two")
        app3 = App(3, "App three", "app3.desktop", "exec_three", "icon_three")
        self._mock_app_datastore.get_all_apps = Mock(return_value = [
                     app1, app2, app3])
        
        self._mock_app_datastore.get_app_by_id = Mock(return_value = app2)
        
        self._test_object.launch_app(2)
        
        self._mock_app_datastore.get_app_by_id.assert_called_once_with(2)
        self._mock_app_launcher.launch.assert_called_once_with("exec_two")
        
    def test_launch_file_should_launch_file_for_associated_app(self):
        app1 = App(1, "App one", "app1.desktop", "exec_one", "icon_one", True)
        app2 = App(2, "App two", "app2.desktop", "exec_two", "icon_two")
        app3 = App(3, "App three", "app3.desktop", "exec_three", "icon_three")
        self._mock_app_datastore.get_all_apps = Mock(return_value = [app1, app2, app3])
        
        self._mock_file_app_associator.associated_app = Mock(return_value = "app1.desktop")

        filename = "test.mp3"
        self._test_object.launch_file(filename)
        
        self._mock_file_app_associator.associated_app.assert_called_with(filename)
        self._mock_app_launcher.launch_file.assert_called_with(filename)
        
    def test_launch_file_should_not_launch_file_if_associated_app_is_not_whitelisted(self):
        app1 = App(1, "App one", "app1.desktop", "exec_one", "icon_one")
        app2 = App(2, "App two", "app2.desktop", "exec_two", "icon_two")
        app3 = App(3, "App three", "app3.desktop", "exec_three", "icon_three")
        self._mock_app_datastore.get_all_apps = Mock(return_value = [app1, app2, app3])
        
        self._mock_file_app_associator.associated_app = Mock(return_value = None)
        self._mock_app_datastore.find_app_by_desktop = Mock(return_value = None)

        filename = "test.mp3"
        self._test_object.launch_file(filename)
        
        self._mock_file_app_associator.associated_app.assert_called_with(filename)
        self.assertTrue(self._mock_app_datastore.find_app_by_desktop.called)
        self.assertFalse(self._mock_app_launcher.launch_file.called)
        
    def test_installed_apps_returns_persisted_apps(self):
        app1 = App(1, "App one", "app1.desktop", "exec_one", "icon_one", True)
        app2 = App(2, "App two", "app2.desktop", "exec_two", "icon_two")
        app3 = App(3, "App three", "app3.desktop", "exec_three", "icon_three")
        app_list = [app1, app2, app3]
        self._mock_app_datastore.get_all_apps = Mock(return_value=app_list)
        self._test_object.get_apps = Mock(return_value=app_list)
        
        apps = self._test_object.get_apps()
        
        self.assertEqual(apps, app_list)
