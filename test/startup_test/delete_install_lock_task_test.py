import unittest
import os

from mock import Mock
from mock import call
from startup.delete_install_lock_task import DeleteInstallLockTask
from startup.auto_updates.force_install import ForceInstall

class DeleteInstallLockTaskTest(unittest.TestCase):
    def setUp(self):
        self._mock_os_utils = Mock()

        self._test_object = DeleteInstallLockTask(self._mock_os_utils)

    def test_delete_lock_removes_lock(self):
        self._test_object.execute()
        
        self._mock_os_utils.remove.assert_called_once_with(ForceInstall.UPGRADE_LOCK)
