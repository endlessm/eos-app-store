import unittest
from mock import Mock, call

from startup.shotwell_tasks import ShotwellTasks

class ShotwellTaskTest(unittest.TestCase):
    def setUp(self):
        mock_manager = Mock()
        self.file_copier = mock_manager.file_copier
        self.home_path_provider = mock_manager.home_path_provider
        self.os_util = mock_manager.os_util

        self.test_object = ShotwellTasks(self.file_copier, self.home_path_provider, self.os_util)

    def test_default_location_is_correct(self):
        self.assertEquals("/usr/share/endlessm-default-files/default_images", self.test_object.SOURCE_DIR)

    def test_gsettings_are_set_for_shotwell(self):
        self.test_object.execute()

        self.os_util.execute.assert_has_calls([
                call(["gsettings", "set", "org.yorba.shotwell.preferences.ui", "show-welcome-dialog", "false"]),
                call(["gsettings", "set", "org.yorba.shotwell.preferences.files", "auto-import", "true"])
                ])

    def test_file_copier_is_called_with_default_images_folder(self):
        pictures_directory = "this is the pictures directory"
        self.home_path_provider.get_pictures_directory = Mock(return_value=pictures_directory)

        self.test_object.execute()

        self.file_copier.assert_called_once_with(self.test_object.SOURCE_DIR, pictures_directory)
