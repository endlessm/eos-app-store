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
        self.initial_shortcuts = [self.available_apps[1],self.available_apps[2], self.available_apps[4]]
        self.mock_app_util = Mock(AppUtil)
        self.mock_app_util.installed_apps = Mock(return_value=self.initial_shortcuts)
        self.mock_app_util.get_available_apps = Mock(return_value=self.available_apps)
        self.mock_app_launcher = Mock(AppLauncher)
        
  
        self.testObject = EndlessDesktopModel(self.mock_app_util, self.mock_app_launcher)
    
    def test_initially_shortcut_list_is_retrieved_from_app_util_manager(self):
        self.assertEqual(self.initial_shortcuts, self.testObject.get_shortcuts())

    def test_get_menus_lists_apps_names_that_are_not_installed(self):
        menu_list = self.testObject.get_menus()

        self.assertEqual(2, len(menu_list))

        for app in [self.available_apps[0], self.available_apps[5]]:
            self.assertTrue(app in menu_list)
            
    def test_add_item_adds_it_to_the_persistence_and_updates_the_list(self):
        shortcut = Mock()
        self.mock_app_util.installed_apps = Mock(return_value=[shortcut])
        
        self.testObject.add_item(shortcut)
        
        self.mock_app_util.save.assert_called_once_with(shortcut)
        self.assertEqual([shortcut], self.testObject.get_shortcuts())
        
    def test_remove_item_updates_persistence_and_updates_the_list(self):
        app_list = [Mock()]
        self.mock_app_util.installed_apps = Mock(return_value=app_list)
        
        self.testObject.remove_item("id1")
        
        self.mock_app_util.remove.assert_called_once_with("id1")
        self.assertEqual(app_list, self.testObject.get_shortcuts())
        
    def test_rename_item_saves_the_changed_item_and_updates_the_list(self):
        shortcut = Mock()
        app_list = [shortcut]
        self.mock_app_util.installed_apps = Mock(return_value=app_list)
        
        self.testObject.rename_item(shortcut, "title")
        
        self.mock_app_util.rename.assert_called_once_with(shortcut, "title")
        self.assertEqual(app_list, self.testObject.get_shortcuts())
        
    def test_reorder_shotrcuts_saves_reordered_list(self):
        self.testObject.reorder_shortcuts(["345", "234", "567"])
        
        self.mock_app_util.save_all.assert_called_once_with([
                                                             self.initial_shortcuts[1], 
                                                             self.initial_shortcuts[0], 
                                                             self.initial_shortcuts[2]])
        
    def test_reorder_shotrcuts_updates_list(self):
        apps = []
        self.mock_app_util.installed_apps = Mock(return_value=apps)
        
        self.testObject.reorder_shortcuts(["345"])
        
        self.assertEqual(apps, self.testObject.get_shortcuts())

    def test_execute_app_with_id_calls_launc_app_on_app_util(self):
        self.testObject.execute_app_with_id('123')
        
        self.mock_app_util.launch_app.assert_called_once_with(123)
        
    def test_launch_search_launches_browser_with_search_string(self):
        search_string = "foo"
        
        self.testObject.launch_search(search_string)
        
        self.mock_app_launcher.launch_browser.assert_called_once_with(search_string)

