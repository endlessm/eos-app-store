import unittest
from subprocess import Popen

from notification_panel.all_settings_model import AllSettingsModel

class TestAllSettingsModel(unittest.TestCase):
    def test_get_current_version_shows_whatever_is_in_version_file(self):
        test_file = "/tmp/test_file.txt"
        current_version = "endless os version"

        with open(test_file, "w") as f:
            f.write(current_version)

        test_object = AllSettingsModel(test_file)
        self.assertEquals(current_version, test_object.get_current_version())

