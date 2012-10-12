import unittest
from mock import Mock, patch
from desktop.endless_desktop_presenter import DesktopPresenter

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
        self.mock_model.get_background_pixbuf = Mock(return_value=pixbuf)
        
        self.testObject.change_background(pixbuf)
        
        self.mock_model.set_background.assert_called_once_with(pixbuf)
        self.mock_view.set_background_pixbuf.assert_called_once_with(pixbuf)
        
    def test_revert_background_sets_background_to_default(self):
        filename = "default"
        self.mock_model.get_default_background = Mock(return_value=filename)
        self.testObject.change_background = Mock()

        self.testObject.revert_background()
        
        self.testObject.change_background.assert_called_once_with(filename)
        
    def test_relocate_item_invalid(self):
        self.mock_model.relocate_shortcut = Mock(return_value=None)
        ret = self.testObject.relocate_item('app1', 'folder1')
        self.assertEqual(ret, False)
        self.mock_model.relocate_shortcut.assert_called_once_with('/app1', '/folder1/')
        
    def test_relocate_item_valid(self):
        destination_shortcut = Mock()
        self.mock_model.get_shortcuts = Mock(return_value=[])
        self.mock_view.hide_folder_window = Mock()
        self.mock_view.show_folder_window = Mock()
        self.mock_view.refresh = Mock()
        
        self.mock_model.relocate_shortcut = Mock(return_value=destination_shortcut)
        ret = self.testObject.relocate_item('app1', 'folder1')
        self.assertEqual(ret, True)
        self.mock_model.relocate_shortcut.assert_called_once_with('/app1', '/folder1/')
        self.mock_view.hide_folder_window.assert_called_once()
        self.mock_view.show_folder_window.assert_called_once_with(destination_shortcut)
        self.mock_view.refresh.assert_called_once_with([])
        