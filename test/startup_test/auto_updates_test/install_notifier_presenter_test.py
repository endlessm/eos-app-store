import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier_presenter import InstallNotifierPresenter
from startup.auto_updates.install_notifier_view import InstallNotifierView

class InstallNotifierPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()
        
        self._mock_view.add_listener = Mock(side_effect=self._view_add_listener)
    
    def _view_add_listener(self, *args, **kwargs):
        if args[0] == InstallNotifierView.RESTART_NOW:
            self._restart_now_button_listener = args[1]
        elif args[0] == InstallNotifierView.RESTART_LATER:
            self._restart_later_button_listener = args[1]
    
    def test_ensure_that_display_is_called(self):
        self._mock_view.display = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._mock_view.display.assert_called_once_with()
        
    def test_ensure_that_the_installation_message_is_updated(self):
        installation_message = "this is the installation message"
        
        self._mock_view.set_new_version = Mock()
        self._mock_model.get_new_version = Mock(return_value=installation_message)
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._mock_view.set_new_version.assert_called_once_with(installation_message)
        
    def test_when_restart_now_button_is_pressed_model_install_now_is_called_on_model(self):
        self._mock_model.install_now = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._restart_now_button_listener()
        
        self.assertTrue(self._mock_model.install_now.called)
        
    def test_when_restart_now_button_is_pressed_close_view(self):
        self._mock_view.close = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._restart_now_button_listener()
        
        self.assertTrue(self._mock_view.close)
        
    def test_when_restart_later_button_is_pressed_model_install_later_is_called_on_model(self):
        self._mock_model.install_later = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._restart_later_button_listener()
        
        self.assertTrue(self._mock_model.install_later.called)
        
    def test_when_restart_later_button_is_pressed_close_view(self):
        self._mock_view.close = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._restart_later_button_listener()
        
        self.assertTrue(self._mock_view.close)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        