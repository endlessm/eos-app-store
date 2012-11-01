import unittest
from mock import Mock #@UnresolvedImport
from startup.auto_updates.update_checker import UpdateChecker

class UpdateCheckerTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_latest_version_provider = Mock()
        self._mock_os_util = Mock()
        self._mock_endless_updater = Mock()
        self._test_object = UpdateChecker(self._mock_latest_version_provider, self._mock_os_util, self._mock_endless_updater)
        
    def test_if_current_version_is_less_than_latest_version_do_update(self):
        self._mock_os_util.get_version = Mock(return_value="1.0.13.1")
        self._mock_latest_version_provider.get_latest_version = Mock(return_value="1.0.14")
        self._mock_endless_updater.update = Mock()
        
        self._test_object.check_for_updates()
        
        self._mock_endless_updater.update.assert_called_once_with()
        
    def test_if_current_version_is_same_as_latest_version_do_not_do_update(self):
        self._mock_os_util.get_version = Mock(return_value="13.1")
        self._mock_latest_version_provider.get_latest_version = Mock(return_value="13.1")
        self._mock_endless_updater.update = Mock()
        
        self._test_object.check_for_updates()
        
        self.assertFalse(self._mock_endless_updater.update.called)

    def test_if_current_version_is_greater_than_latest_version_do_not_do_update(self):
        self._mock_os_util.get_version = Mock(return_value="1.0.12")
        self._mock_latest_version_provider.get_latest_version = Mock(return_value="0.0.13.1")
        self._mock_endless_updater.update = Mock()
        
        self._test_object.check_for_updates()
        
        self.assertFalse(self._mock_endless_updater.update.called)
        