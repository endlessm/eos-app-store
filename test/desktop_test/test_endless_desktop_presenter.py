import unittest
from mock import Mock, patch
from desktop.endless_desktop_presenter import DesktopPresenter

class TestEndlessDesktopPresenter(unittest.TestCase):
    def setUp(self):
        self.mock_model = Mock()
        self.mock_view = Mock()
        
        self.testObject = DesktopPresenter(self.mock_view, self.mock_model)
    
    @patch.object(DesktopPresenter, 'refresh_view')
    def test_initially_presenter_forces_a_refresh(self, refresh_view):
        DesktopPresenter(Mock(), Mock())
        
        refresh_view.assert_called_once_with()
    
    @patch.object(DesktopPresenter, 'refresh_view')
    def test_add_item_adds_the_item_and_refreshes_the_view(self, refresh_view):
        shortcut = Mock()
        
        self.testObject.add_item(shortcut)

        self.mock_model.add_item.assert_called_once_with(shortcut)
        refresh_view.assert_called_once_with()

    @patch.object(DesktopPresenter, 'refresh_view')
    def test_remove_item_removes_item_refreshes_view(self, refresh_view):
        shortcut = Mock()
        
        self.testObject.remove_item(shortcut)
        
        self.mock_model.remove_item.assert_called_once_with(shortcut)
        refresh_view.assert_called_once_with()
        
    @patch.object(DesktopPresenter, 'refresh_view')
    def test_move_item_moves_item_and_refreshes_view(self, refresh_view):
        indexes = Mock()
        
        self.testObject.move_item(indexes)
        
        self.mock_model.reorder_shortcuts.assert_called_once_with(indexes)
        refresh_view.assert_called_once_with()

    def test_rename_item_updates_model(self):
        shortcut = Mock()
        name = "name"
        
        self.testObject.rename_item(shortcut, name)
        
        self.mock_model.rename_item.assert_called_once_with(shortcut, name)
    
    def test_activate_item_invokes_process(self):
        shortcut = Mock()
        
        self.testObject.activate_item(shortcut)
        
        self.mock_model.execute_app_with_id.assert_called_once_with(shortcut)
        
    def test_refresh_view_updates_view(self):
        mock_shortcuts = [Mock(), Mock()]
        mock_menus = [Mock(), Mock()]
        self.mock_view.refresh = Mock()
        self.mock_view.populate_popups = Mock()
        self.mock_model.get_shortcuts = Mock(return_value=mock_shortcuts)
        self.mock_model.get_menus = Mock(return_value=mock_menus)
        
        self.testObject.refresh_view()
        
        self.mock_view.refresh.assert_called_once_with(mock_shortcuts)
        self.mock_view.populate_popups.assert_called_once_with(mock_menus)
        
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
        
        
        