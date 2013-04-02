import unittest
from notification_panel.settings_app_presenter import SettingsAppPresenter

class TestSettingsAppPresenter(unittest.TestCase):
    def setUp(self):
        self.testObject = SettingsAppPresenter()

    def test_path_is_correct(self):
        settings_path = "/usr/bin/endless-settings"

        self.assertEquals(settings_path, self.testObject.get_path())

