import unittest

from mock import Mock
from mock import call
from startup.delete_desktop_state_task import DeleteDesktopStateTask
import os

class DeleteDesktopStateTaskTest(unittest.TestCase):
    def setUp(self):
        self._mock_shell_utils = Mock()
        
        self._test_object = DeleteDesktopStateTask(self._mock_shell_utils)
    
    def test_delete_state_removes_state_file(self):
        self._test_object.execute()
        self._mock_shell_utils.rmtree.assert_called_once_with(os.path.expanduser("~/.endlessm/desktop.json"), True)
