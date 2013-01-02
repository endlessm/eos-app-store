import unittest
from mock import Mock, patch
from taskbar_panel.taskbar_presenter import TaskbarPresenter
from osapps.app_shortcut import AppShortcut

class TestTaskbarPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_app_launcher = Mock()

        self.testObject = TaskbarPresenter(self.mock_app_launcher)

    def tearDown(self):
        pass

    def test_launch_search_launches_search(self):
        search_string = "blah"

        self.testObject.launch_search(search_string)

        self.mock_app_launcher.launch_browser.assert_called_once_with(search_string)



