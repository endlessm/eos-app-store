import unittest
from mock import Mock, patch
from desktop.endless_desktop_presenter import DesktopPresenter
from osapps.app_shortcut import AppShortcut

class TestEndlessDesktopPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_model = Mock()
        self.mock_view = Mock()

        self.testObject = DesktopPresenter(self.mock_view, self.mock_model)

    def tearDown(self):
        self.testObject._view.destroy()


    @patch.object(DesktopPresenter, 'refresh_view')
    def test_initially_presenter_forces_a_refresh(self, refresh_view):
        DesktopPresenter(Mock(), Mock())

        refresh_view.assert_called_once_with()

    def test_activate_item_invokes_process(self):
        shortcut = Mock()
        params = []

        self.testObject.activate_item(shortcut, params)

        self.mock_model.execute_app.assert_called_once_with(shortcut, params)

    def test_refresh_view_updates_view(self):
        mock_shortcuts = [Mock(), Mock()]
        mock_menus = [Mock(), Mock()]
        self.mock_view.refresh = Mock()
        self.mock_view.populate_popups = Mock()
        self.mock_model.get_shortcuts = Mock(return_value=mock_shortcuts)
        self.mock_model.get_menus = Mock(return_value=mock_menus)

        self.testObject.refresh_view()
        
        self.mock_model.get_shortcuts.assert_called_once_with()

        self.mock_view.refresh.assert_called_once_with(mock_shortcuts)

    def test_submit_feedback_updates_model(self):
        message = "some text"
        is_bug = True

        self.testObject.submit_feedback(message, is_bug)

        self.mock_model.submit_feedback.assert_called_once_with(message, is_bug)

    def test_if_refresh_is_occuring_already_do_not_redraw_again(self):
        self.mock_view.refresh = None
        self.testObject._is_refreshing = True

        try:
            self.testObject.refresh_view()
            """Pass"""
        except:
            self.fail("Should not have thrown any errors as no code should have executed")

    def test_launch_search_launches_search(self):
        search_string = "blah"

        self.testObject.launch_search(search_string)

        self.mock_model.launch_search.assert_called_once_with(search_string)

    def test_change_background_sets_background(self):
        self.mock_model.reset_mock()
        self.mock_view.reset_mock()

        pixbuf = "pixbuf"
        self.mock_model.get_background_image = Mock(return_value=pixbuf)

        self.testObject.change_background(pixbuf)

        self.mock_model.set_background.assert_called_once_with(pixbuf)
        self.mock_view.set_background_image.assert_called_once_with(pixbuf)

    def test_revert_background_sets_background_to_default(self):
        filename = "default"
        self.mock_model.get_default_background = Mock(return_value=filename)
        self.testObject.change_background = Mock()

        self.testObject.revert_background()

        self.testObject.change_background.assert_called_once_with(filename)

    def test_delete_shortcut(self):
        shortcut = "shortcut"
        self.testObject.delete_shortcut(shortcut)
        self.mock_model.delete_shortcut.assert_called_once_with(shortcut)

    def test_rename_shortcut(self):
        shortcut = AppShortcut(123, "App 1", "", [])
        new_name = 'Blah'
        self.mock_model.get_shortcuts_from_cache = Mock(return_value=[shortcut])
        changed_shortcut = self.testObject.rename_shortcut(shortcut, new_name)
        self.mock_model.set_shortcuts.assert_called_once()
        self.assertEqual(changed_shortcut.name(), new_name)

    def test_check_shortcut_name(self):
        shortcut1 = AppShortcut(123, "App", "", [])
        shortcut2 = AppShortcut(123, "App 1", "", [])
        self.mock_model.get_shortcuts = Mock(return_value=[shortcut1, shortcut2])
        expected_value = 'App 2'
        self.assertEqual(expected_value, self.testObject.check_shortcut_name('App', self.mock_model.get_shortcuts()))

    def test_relocate_item(self):
        self.mock_model.relocate_shortcut = Mock(return_value=True)
        source_shortcut = Mock()
        folder_shortcut = Mock()

        ret = self.testObject.relocate_item(source_shortcut, folder_shortcut)
        self.assertEqual(ret, True)

        self.mock_model.relocate_shortcut.assert_called_once_with(
            source_shortcut,
            folder_shortcut
            )

    def test_get_shortcut_by_name(self):
        app1 = Mock()
        app1.name = Mock(return_value='app 1')
        app2 = Mock()
        app2.name = Mock(return_value='app 2')
        app3 = Mock()
        app3.name = Mock(return_value='app 3')
        self.testObject._model.get_shortcuts_from_cache = Mock(return_value=[app1, app2, app3])

        app_ret = self.testObject.get_shortcut_by_name('app 1')
        self.assertEqual(app_ret, app1)

        app_ret = self.testObject.get_shortcut_by_name('app 2')
        self.assertEqual(app_ret, app2)

        app_ret = self.testObject.get_shortcut_by_name('app 3')
        self.assertEqual(app_ret, app3)

        app_ret = self.testObject.get_shortcut_by_name('app 4')
        self.assertEqual(app_ret, None)


    def test_rearrange_shortcuts_no_relocate(self):
        self.testObject._model.get_shortcuts = Mock(return_value=None)
        source_shortcut = Mock()
        source_shortcut.parent = Mock(return_value = None)
        self.testObject.relocate_item = Mock()

        self.testObject.rearrange_shortcuts(source_shortcut, None, None)

        self.assertFalse(self.testObject.relocate_item.called)

    def test_rearrange_shortcuts_relocate(self):
        self.testObject._model.get_shortcuts = Mock(return_value=None)
        source_shortcut = Mock()
        source_shortcut.parent = Mock(return_value = Mock())
        self.testObject.relocate_item = Mock()

        self.testObject.rearrange_shortcuts(source_shortcut, None, None)

        self.testObject.relocate_item.assert_called_once_with(source_shortcut, None)

    def test_rearrange_shortcuts_left_destination(self):
        all_shortcuts = Mock()
        self.testObject._model.get_shortcuts_from_cache = Mock(return_value=all_shortcuts)
        source_shortcut = Mock()
        source_shortcut.parent = Mock(return_value = None)
        left_shortcut = Mock()
        self.testObject.move_item_left = Mock()
        self.testObject.move_item = Mock()
        self.testObject.move_item_right = Mock()

        self.testObject.rearrange_shortcuts(source_shortcut, left_shortcut, None)

        self.testObject.move_item_left.assert_called_once_with(source_shortcut, left_shortcut, all_shortcuts)
        self.testObject.move_item.assert_called_once_with(all_shortcuts)
        self.assertFalse(self.testObject.move_item_right.called)

    def test_rearrange_shortcuts_right_destination(self):
        all_shortcuts = Mock()
        self.testObject._model.get_shortcuts_from_cache = Mock(return_value=all_shortcuts)
        source_shortcut = Mock()
        source_shortcut.parent = Mock(return_value = None)
        right_shortcut = Mock()
        self.testObject.move_item_right = Mock()
        self.testObject.move_item = Mock()
        self.testObject.move_item_left = Mock()

        self.testObject.rearrange_shortcuts(source_shortcut, None, right_shortcut)

        self.testObject.move_item_right.assert_called_once_with(source_shortcut, right_shortcut, all_shortcuts)
        self.testObject.move_item.assert_called_once_with(all_shortcuts)
        self.assertFalse(self.testObject.move_item_left.called)

    def test_move_item_right_source_on_desk(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_1, sc_2, sc_3]

        self.testObject.move_item_right(sc_1, sc_3, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_1, sc_3])

    def test_move_item_right_source_not_on_desk(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_2, sc_3]

        self.testObject.move_item_right(sc_1, sc_3, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_1, sc_3])

    def test_move_item_left_source_on_desk_place_on_end(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_1, sc_2, sc_3]

        self.testObject.move_item_left(sc_1, sc_3, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_3, sc_1])

    def test_move_item_left_source_on_desk_place_in_between(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_1, sc_2, sc_3]

        self.testObject.move_item_left(sc_1, sc_2, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_1, sc_3])

    def test_move_item_left_source_not_on_desk_place_on_end(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_2, sc_3]

        self.testObject.move_item_left(sc_1, sc_3, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_3, sc_1])

    def test_move_item_left_source_not_on_desk_place_in_between(self):
        sc_1 = Mock()
        sc_2 = Mock()
        sc_3 = Mock()
        all_shortcuts = [sc_1, sc_2, sc_3]

        self.testObject.move_item_left(sc_1, sc_2, all_shortcuts)

        self.assertEqual(all_shortcuts, [sc_2, sc_1, sc_3])



