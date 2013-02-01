import unittest
from notification_panel.all_settings_presenter import AllSettingsPresenter

class TestAllSettingsPresenter(unittest.TestCase):
    def setUp(self):
        self.testObject = AllSettingsPresenter()

    def test_path_is_correct(self):
        settings_path = "/usr/bin/endless-settings"

        self.assertEquals(settings_path, self.testObject.get_path())

