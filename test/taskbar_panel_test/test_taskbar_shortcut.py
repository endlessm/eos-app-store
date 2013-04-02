import unittest
from mock import Mock
from taskbar_panel.taskbar_shortcut import TaskbarShortcut
import os

class TestTaskbarShortcut(unittest.TestCase):
    def setUp(self):
        self.test_object = TaskbarShortcut()
        
    def test_display_when_file_does_not_exist(self):
        self.assertFalse(self.test_object.is_launcher_present("/no_here"))

    def test_display_when_file_does_exist(self):
        self.assertTrue(self.test_object.is_launcher_present(self._path()))
        
    def _path(self):
        return os.path.realpath(__file__)         