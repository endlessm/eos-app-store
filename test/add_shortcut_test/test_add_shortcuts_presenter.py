import unittest
from mock import Mock
from add_shortcuts_module.add_shortcuts_presenter import AddShortcutsPresenter
from add_shortcuts_module.add_shortcuts_model import AddShortcutsModel
from osapps.app_shortcut import AppShortcut

class TestAddShortcutsPresenter(unittest.TestCase):
    
    def setUp(self):
        self.mock_model = Mock()
        self.test_object = AddShortcutsPresenter()
        self.test_object._model = self.mock_model
        self.mock_presenter = Mock()
        
        self.path = '/tmp/'
        self.hint = 'blah'
        self.available_app_shortcuts = [
                                        AppShortcut(123, "App", "", []),
                                        AppShortcut(234, "App 1", "", []),
                                        AppShortcut(345, "App 2", "", [])
                                        ]
        
        self.mock_presenter._model._app_desktop_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        self.mock_presenter._model._app_desktop_datastore.add_shortcut = Mock()
        
    def test_get_category_data(self):
        self.test_object.get_category_data()
        self.mock_model.get_category_data.assert_called_once_with()
        
    def test_get_folder_icons(self):
        self.test_object.get_folder_icons(self.path, self.hint)
        self.mock_model.get_folder_icons.assert_called_once_with(self.path, self.hint)
    
    def test_create_directory(self):
        dir_name = 'blah'
        self.test_object.create_directory(dir_name, '/tmp/image.svg', self.mock_presenter)
        self.mock_model.create_directory.assert_called_once_with(dir_name)
        self.mock_presenter._model._app_desktop_datastore.get_all_shortcuts.assert_called_once_with()
        self.mock_presenter._model._app_desktop_datastore.add_shortcut.assert_called_once()
    
    def test_check_dir_name(self):
        expected_value = 'App 3'
        self.assertEqual(expected_value, self.test_object.check_dir_name('App', self.available_app_shortcuts))