import unittest
from mock import Mock

from startup.firefox_tasks import FirefoxTasks

class FirefoxTaskTest(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.file_copier = self.mock_manager.file_copier
        self.home_path_provider = self.mock_manager.home_path_provider

        self.test_object = FirefoxTasks(self.file_copier, self.home_path_provider)

    def test_constants_have_correct_values(self):
        self.assertEquals("/etc/eos-browser/mozilla", self.test_object.SOURCE_DIR)
        self.assertEquals(".mozilla", self.test_object.TARGET_DIR)

    def test_file_copier_is_called_with_default_config_folder(self):
        user_directory = "this is the user directory"
        self.home_path_provider.get_user_directory = Mock(return_value=user_directory)

        self.test_object.execute()

        self.file_copier.assert_called_once_with(self.test_object.SOURCE_DIR, user_directory)

    def test_home_path_provider_is_given_correct_folder(self):
        self.test_object.execute()

        self.home_path_provider.get_user_directory.assert_called_once_with(self.test_object.TARGET_DIR)

