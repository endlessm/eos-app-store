import unittest
from mock import Mock

from startup.firefox_tasks import FirefoxTasks

class FirefoxTaskTest(unittest.TestCase):
    def setUp(self):
        self.home_directory_copier = Mock()
        self.os_util = Mock()
        self.os_util.execute = Mock()
        self.home_path = "home_path"
        self.home_path_provider = Mock(return_value =
                self.home_path)

        self.test_object = FirefoxTasks(self.home_directory_copier, self.os_util)

    def test_default_location_is_correct(self):
        self.assertEquals("/etc/endlessm/mozilla",
                self.test_object._default_config_folder_path())

    def test_target_dir_is_correct(self):
        self.assertEqual('.mozilla', self.test_object.TARGET_DIR)

    def test_file_copier_is_called_with_default_config_folder(self):
        self.test_object.execute()
        self.home_directory_copier.copy_from.assert_called_once_with(self.test_object._default_config_folder_path())
