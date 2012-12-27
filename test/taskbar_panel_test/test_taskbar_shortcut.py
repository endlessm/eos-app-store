import unittest
from mock import Mock
from taskbar_panel.taskbar_shortcut import TaskbarShortcut
import os

class TestTaskbarShortcut(unittest.TestCase):
    def test_display_when_file_does_not_exist(self):
        view = Mock()
        test_object = TaskbarShortcut(view, "/no_here")
        callback = Mock()
        
        test_object.display(callback)
        
        callback.assert_was_not_called()

    def test_display_when_file_does_exist(self):
        view = Mock()
        test_object = TaskbarShortcut(view, self._path())
        callback = Mock()
        
        test_object.display(callback)
        
        callback.assert_was_called_once_with(view)
        
    def _path(self):
        return os.path.realpath(__file__)         