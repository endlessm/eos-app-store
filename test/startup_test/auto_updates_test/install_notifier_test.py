import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier import InstallNotifier
from startup.auto_updates.install_notifier_model import InstallNotifierModel

class InstallNotifierTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_install_notifier_model = Mock()
        
        self._mock_install_notifier_model.add_listener = Mock(side_effect=self._model_add_listener)
        
        self._test_object = InstallNotifier(self._mock_install_notifier_model)
        
    def _model_add_listener(self, *args, **kwargs):
        if args[0] == InstallNotifierModel.ACTION_TAKEN:
            self._model_action_taken_listener = args[1]
    
    def test_should_install_is_pass_through_to_given_model_when_returns_true(self):
        self._mock_install_notifier_model.should_install = Mock(return_value=True)
        
        self.assertTrue(self._test_object.should_install())

    def test_should_install_is_pass_through_to_given_model_when_returns_False(self):
        self._mock_install_notifier_model.should_install = Mock(return_value=False)
        
        self.assertFalse(self._test_object.should_install())

    def test_when_model_notifies_action_taken_then_notify_listeners(self):
        listener = Mock()
        
        self._test_object.add_listener(InstallNotifier.USER_RESPONSE, listener)
        
        self._model_action_taken_listener()
        
        self.assertTrue(listener.called)

