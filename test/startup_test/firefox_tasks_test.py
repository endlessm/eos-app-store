import unittest
from mock import Mock

from startup.firefox_tasks import FirefoxTasks

class FirefoxTaskTest(unittest.TestCase):
    def setUp(self):
        self.home_directory_copier = Mock()

        self.test_object = FirefoxTasks(self.home_directory_copier)

    def test_constants_have_correct_values(self):
        self.assertEquals("/etc/eos-browser/mozilla", self.test_object.SOURCE_DIR)
        self.assertEquals(".mozilla", self.test_object.TARGET_DIR)

    def test_file_copier_is_called_with_default_config_folder(self):
        self.test_object.execute()

        self.home_directory_copier.copy.assert_called_once_with(self.test_object.SOURCE_DIR, self.test_object.TARGET_DIR)
