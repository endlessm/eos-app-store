import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier_model import InstallNotifierModel

class InstallNotifierModelTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_latest_version_provider = Mock()
        self._test_object = InstallNotifierModel(self._mock_latest_version_provider)
    
    def test_get_new_version_returns_version_from_latest_version_provider(self):
        new_version = "1.0.12~rc4; this is the new; version"
        
        self._mock_latest_version_provider.get_latest_version = Mock(return_value=new_version)
        
        self.assertEquals("1.0.12~rc4", self._test_object.get_new_version())
        
    def test_when_install_now_is_called_then_should_install_returns_true(self):
        self._test_object.install_now()
        
        self.assertTrue(self._test_object.should_install())
        
    def test_when_install_later_is_called_then_should_install_returns_false(self):
        self._test_object.install_later()
        
        self.assertFalse(self._test_object.should_install())
        
    def test_when_install_later_is_called_then_action_taken_listeners_are_notified(self):
        listener = Mock()
        self._test_object.add_listener(InstallNotifierModel.ACTION_TAKEN, listener)
        
        self._test_object.install_later()
        
        self.assertTrue(listener.called)
        
    def test_when_install_now_is_called_then_action_taken_listeners_are_notified(self):
        listener = Mock()
        self._test_object.add_listener(InstallNotifierModel.ACTION_TAKEN, listener)
        
        self._test_object.install_now()
        
        self.assertTrue(listener.called)
