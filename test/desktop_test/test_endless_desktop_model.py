import unittest
from desktop.endless_desktop_model import EndlessDesktopModel
from mock import Mock #@UnresolvedImport
from osapps.app_launcher import AppLauncher
#from osapps.app import App
from osapps.app_shortcut import AppShortcut
from osapps.desktop_locale_datastore import DesktopLocaleDatastore
from osapps.app_datastore import AppDatastore
from osapps.launchable_app import LaunchableApp
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from desktop.list_paginator import ListPaginator

class DesktopModelTestCase(unittest.TestCase):
    def setUp(self):
        self.available_app_shortcuts = [
                                        AppShortcut(123, "App 1", "", []),
                                        AppShortcut(234, "App 2", "", []),
                                        AppShortcut(345, "App 3", "", [])
                                        ]
        self.mock_desktop_locale_datastore = Mock(DesktopLocaleDatastore)
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        self.mock_app_datastore = Mock(AppDatastore)
        self.app_mock = Mock(LaunchableApp)
        self.app_mock.executable = Mock(return_value="eog")
        self.mock_app_datastore.get_app_by_key = Mock(return_value=self.app_mock)
        self.mock_app_launcher = Mock(AppLauncher)
        self.mock_desktop_preferences = Mock(DesktopPreferencesDatastore)
        self.mock_paginator = Mock(ListPaginator)
        self.testObject = EndlessDesktopModel(self.mock_desktop_locale_datastore,
                                              self.mock_desktop_preferences,
                                              self.mock_app_datastore,
                                              self.mock_app_launcher,
                                              paginator=self.mock_paginator
                                              )

    def test_execute_app_with_id_calls_launc_app_on_app_util(self):
        params = []
        self.testObject.execute_app('123', params)

        self.mock_app_launcher.launch_desktop.assert_called_once_with("123", params)

    def test_execute_app_with_cannot_find_app_no_exception(self):
        self.mock_app_datastore = Mock(AppDatastore)
        self.mock_app_datastore.get_app_by_key = Mock(return_value=None)
        self.testObject = EndlessDesktopModel(self.mock_desktop_locale_datastore,
                                              self.mock_desktop_preferences,
                                              self.mock_app_datastore,
                                              self.mock_app_launcher
                                              )

        params = []
        self.testObject.execute_app('123', params)

        self.assertFalse(self.mock_app_launcher.launch.called)

    def test_get_background_delegates_to_preferences_datastore(self):
        self.testObject.get_background_image()

        self.mock_desktop_preferences.get_background_image.assert_called()

    def test_set_background_delegates_to_preferences_datastore(self):
        expected = "/foo/whatever/blah"
        self.testObject.set_background(expected)

        self.mock_desktop_preferences.set_background.assert_called_once_with(expected)

    def test_get_default_background_delegates_to_preferences_datastore(self):
        self.testObject.get_default_background()

        self.mock_desktop_preferences.get_default_background.assert_called()

    def test_delete_shortcut_exists(self):
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        app1 = self.available_app_shortcuts[0]
        self.assertEqual(self.testObject.delete_shortcut(app1), True, 'Delete shortcut which exists FAILED.')

    def test_delete_shortcut_does_not_exist(self):
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        invalid_app = AppShortcut(223, "App 5", "", [])
        self.assertEqual(self.testObject.delete_shortcut(invalid_app), False, 'Delete shortcut which does not exist FAILED.')

    def test_delete_shortcut_exception_handled(self):
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        self.mock_desktop_locale_datastore.set_all_shortcuts = Mock(side_effect=Exception('Booom!'))
        #self.mock_desktop_locale_datastore.set_all_shortcuts()
        app1 = self.available_app_shortcuts[0]
        self.assertEqual(self.testObject.delete_shortcut(app1), False, 'Delete shortcut, exception handled FAILED.')

    def test_relocate_shortcut_invalid_source(self):
        ret = self.testObject.relocate_shortcut(None, 'irrelevant')
        self.assertEqual(ret, False)

    def test_relocate_shortcut_move_to_root(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        app1.add_child(app2)
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1])
        self.testObject._relocate_shortcut_to_root = Mock(return_value=[app1])

        ret = self.testObject.relocate_shortcut(app2, None)

        self.testObject._relocate_shortcut_to_root.assert_called_once_with(app2)

    def test_relocate_shortcut_move_to_root_source_already_on_root(self):
        app1 = AppShortcut('', 'app1', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1])
        self.testObject._relocate_shortcut_to_root = Mock()
        self.testObject._relocate_shortcut_to_folder = Mock()

        ret = self.testObject.relocate_shortcut(app1, None)

        self.assertFalse(self.testObject._relocate_shortcut_to_root.called)
        self.assertFalse(self.testObject._relocate_shortcut_to_folder.called)
        self.assertEqual(ret, False)

    def test_relocate_shortcut_move_to_folder(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        app1.add_child(app2)
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1])
        self.testObject._relocate_shortcut_to_root = Mock()
        self.testObject._relocate_shortcut_to_folder = Mock()

        ret = self.testObject.relocate_shortcut(app1, app2)

        self.testObject._relocate_shortcut_to_folder.assert_called_once_with(app1, app2)
        self.assertFalse(self.testObject._relocate_shortcut_to_root.called)

    def test_relocate_shortcut_to_root(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        app3 = AppShortcut('', 'app3', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1])
        self.mock_desktop_locale_datastore.set_all_shortcuts = Mock()
        app3.add_child(app2)

        ret = self.testObject._relocate_shortcut_to_root(app2)

        self.mock_desktop_locale_datastore.set_all_shortcuts.assert_called_once_with([app1, app2])
        self.assertTrue(ret)
        self.assertEqual(app3.children(), [])

    def test_relocate_shortcut_to_folder_not_desk_no_parent(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[])
        self.mock_desktop_locale_datastore.set_all_shortcuts = Mock()

        ret = self.testObject._relocate_shortcut_to_folder(app1, app2)
        self.assertFalse(ret)
        self.assertFalse(self.mock_desktop_locale_datastore.set_all_shortcuts.called)

    def test_relocate_shortcut_to_folder_on_desk_no_parent(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1, app2])
        self.mock_desktop_locale_datastore.set_all_shortcuts = Mock()

        ret = self.testObject._relocate_shortcut_to_folder(app1, app2)
        self.assertTrue(ret)
        self.mock_desktop_locale_datastore.set_all_shortcuts.assert_called_once_with([app2])
        self.assertEqual(app2.children(), [app1])

    def test_relocate_shortcut_to_folder_have_parent_to_folder(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        app3 = AppShortcut('', 'app3', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1])
        self.mock_desktop_locale_datastore.set_all_shortcuts = Mock()
        app3.add_child(app1)

        all_shortcuts = self.mock_desktop_locale_datastore.get_all_shortcuts()

        ret = self.testObject._relocate_shortcut_to_folder(app1, app2)
        self.assertTrue(ret)
        self.assertEqual(app3.children(), [])
        self.assertEqual(app2.children(), [app1])
        self.mock_desktop_locale_datastore.set_all_shortcuts.assert_called_once_with(all_shortcuts)

    def test_relocate_shortcut_to_folder_destination(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=[app1, app2])

        ret = self.testObject.relocate_shortcut(app1, app2)
        self.assertEqual(ret, True)
        self.assertEqual(app1.parent(), app2)
        self.assertTrue(app1 in app2.children())

    def test_relocate_shortcut_to_desk_destination(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(
            return_value=[app1, app2]
            )
        app1._parent = app2

        ret = self.testObject.relocate_shortcut(app1, None)
        self.assertEqual(ret, True)
        self.assertEqual(app1.parent(), None)
        self.assertTrue(app2 not in app1.children())
        
    def test_get_paginated_shortcuts(self):
        app1 = AppShortcut('', 'app1', '')
        app2 = AppShortcut('', 'app2', '')
        app3 = AppShortcut('', 'app3', '')
        all_shortcuts = [app1, app2, app3]
        self.mock_desktop_locale_datastore.get_all_shortcuts = Mock(return_value=all_shortcuts)
        self.mock_paginator.current_page = Mock(return_value=[app1])

        shortcuts = self.testObject.get_shortcuts()
        
        self.mock_paginator.adjust_list_of_items.assert_called_once_with(all_shortcuts)
        
        self.mock_paginator.current_page.assert_called_once_with()
        self.assertEquals(shortcuts, [app1])
        
    def test_get_current_page_index(self):
        self.mock_paginator.current_page_index = Mock(return_value=1)
        
        self.assertEquals(1, self.testObject.get_page_index())
        
        self.mock_paginator.current_page_index.assert_called_once_with()

    def test_get_next_page_of_shortcuts(self):
        self.testObject.next_page()
        
        self.mock_paginator.next.assert_called_once_with()
        
    def test_get_previous_page_of_shortcuts(self):
        self.testObject.previous_page()
        
        self.mock_paginator.prev.assert_called_once_with()
        
    def test_get_page_by_index(self):
        page_index = 3
        
        self.testObject.go_to_page(page_index)
        
        self.mock_paginator.go_to_page.assert_called_once_with(page_index)
        
    def test_get_total_pages(self):
        page_count = 3
        self.mock_paginator.number_of_pages = Mock(return_value=page_count)
        
        self.assertEquals(page_count,self.testObject.get_total_pages())
        
        self.mock_paginator.number_of_pages.assert_called_once_with()

        
        
