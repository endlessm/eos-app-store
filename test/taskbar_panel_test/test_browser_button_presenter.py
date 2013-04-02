import unittest
from mock import Mock

from taskbar_panel.browser_button_constants import BrowserButtonConstants
from taskbar_panel.browser_button_presenter import BrowserButtonPresenter

class BrowserButtonPresenterTest(unittest.TestCase):
   def setUp(self):
      mock_master = Mock()
      self._mock_view = mock_master.view()
      self._mock_model = mock_master.model()
      self._mock_browser_launcher = mock_master.browser_launcher()
      self._mock_view.add_listener = Mock(side_effect=self._view_add_listener_side_effect)

      BrowserButtonPresenter(self._mock_view, self._mock_model, self._mock_browser_launcher)

   def _view_add_listener_side_effect(self, *args, **kwargs):
      if args[0] == BrowserButtonConstants.CLICK_EVENT:
         self._handle_click_event = args[1]

   def test_when_view_is_clicked_launch_browser_with_url_from_model(self):
      url = "some url"
      self._mock_model.get_exploration_center_url = Mock(return_value=url)

      self._handle_click_event()

      self.assertFalse(self._mock_model.get_exploration_center_url.called)
      self._mock_browser_launcher.launch_browser.assert_called_once_with()
