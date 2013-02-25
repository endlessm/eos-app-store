import unittest
from mock import Mock, call

from util.rename_widget_constants import RenameWidgetConstants
from util.rename_widget_presenter import RenameWidgetPresenter

class RenameWidgetPresenterTest(unittest.TestCase):
    def setUp(self):
        self._mock_master = Mock()
        self._mock_view = self._mock_master.view
        self._mock_model = self._mock_master.model

        self._mock_view.add_listener = Mock(side_effect=self._view_event_listener)


    def _view_event_listener(self, *args, **kwargs):
        if args[0] == RenameWidgetConstants.RETURN_PRESSED:
            self._return_pressed = args[1]
        elif args[0] == RenameWidgetConstants.ESCAPE_PRESSED:
            self._escape_pressed = args[1]

    def test_presenter_executes_initial_setup(self):
        original_name = 'original name'
        self._mock_model.get_original_name = Mock(return_value=original_name)

        RenameWidgetPresenter(self._mock_view, self._mock_model)

        self._mock_view.set_original_name.assert_called_once_with(original_name)
        self.assertTrue(self._mock_view.resize_window.called)
        self.assertTrue(self._mock_view.show_window.called)

    def test_save_new_name_when_return_is_pressed(self):
        RenameWidgetPresenter(self._mock_view, self._mock_model)

        new_name = 'this is the new name'
        self._mock_view.get_new_name = Mock(return_value=new_name)

        self._return_pressed()

        self._mock_model.save.assert_called_once_with(new_name)

    def test_close_view_when_return_is_pressed(self):
        RenameWidgetPresenter(self._mock_view, self._mock_model)

        self._return_pressed()

        self.assertTrue(self._mock_view.close_window.called)

    def test_close_window_when_escape_is_pressed(self):
        RenameWidgetPresenter(self._mock_view, self._mock_model)

        self._escape_pressed()

        self.assertTrue(self._mock_view.close_window.called)
