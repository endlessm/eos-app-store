import unittest
from mock import Mock, patch
from notification_panel.all_settings_presenter import AllSettingsPresenter
from osapps.app_shortcut import AppShortcut

class TestAllSettingsPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_app_launcher = Mock()

        self.testObject = AllSettingsPresenter(self.mock_app_launcher)

    def tearDown(self):
        pass

    def test_launch_settings_launches_settings(self):
        settings_path = "/usr/bin/eos-settings"

        self.testObject.launch()

        self.mock_app_launcher.launch.assert_called_once_with(settings_path)
