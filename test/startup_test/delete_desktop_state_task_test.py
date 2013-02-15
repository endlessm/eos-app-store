import unittest

from mock import Mock
from mock import call
from startup.delete_desktop_state_task import DeleteDesktopStateTask
import os

class DeleteDesktopStateTaskTest(unittest.TestCase):
    def setUp(self):
        self._mock_os_utils = Mock()
        self._mock_sh_utils = Mock()

        self._test_object = DeleteDesktopStateTask(self._mock_os_utils, self._mock_sh_utils)

    def test_delete_state_removes_state_file(self):
        self._test_object.execute()

        calls = [call(os.path.expanduser("~/.endlessm/desktop.json"))]
        self._mock_sh_utils.copyfile.assert_called_once_with("/etc/endlessm/installed_applications.json", os.path.expanduser("~/.endlessm/installed_applications.json"))
        self._mock_os_utils.remove.assert_has_calls(calls)



