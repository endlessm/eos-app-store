import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier import InstallNotifier

class InstallNotifierTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_install_notifier_model = Mock()
        self._test_object = InstallNotifier(self._mock_install_notifier_model)
    
    def test_should_install_is_pass_through_to_given_model_when_returns_true(self):
        self._mock_install_notifier_model.should_install = Mock(return_value=True)
        
        self.assertTrue(self._test_object.should_install())

    def test_should_install_is_pass_through_to_given_model_when_returns_False(self):
        self._mock_install_notifier_model.should_install = Mock(return_value=False)
        
        self.assertFalse(self._test_object.should_install())



