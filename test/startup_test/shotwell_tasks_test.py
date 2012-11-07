import unittest
from startup.tasks import Tasks
from mock import Mock, call
import shutil
import os
import os.path

from startup.shotwell_tasks import ShotwellTasks

class ShotwellTaskTest(unittest.TestCase):
    def setUp(self):
        self.home_directory_copier = Mock()
        self.os_util = Mock()
        self.os_util.execute = Mock()
        self.home_path = "home_path"
        self.home_path_provider = Mock(return_value =
                self.home_path)

        self.test_object = ShotwellTasks(self.home_path_provider,
                self.home_directory_copier, self.os_util)

    def test_default_location_is_correct(self):
        self.assertEquals("/usr/share/endlessm/default_images",
                self.test_object.IMAGES_FOLDER_PATH)

    def test_target_dir_is_correct(self):
        self.assertEqual('Pictures', self.test_object.TARGET_DIR)

    def test_gsettings_are_set_for_shotwell(self):
        self.test_object.execute()
        self.os_util.execute.assert_has_calls([
                call(["gsettings", "set", "org.yorba.shotwell.preferences.ui", "show-welcome-dialog", "false"]),
                call(["gsettings", "set", "org.yorba.shotwell.preferences.files", "auto-import", "true"])
                ])

    def test_file_copier_is_called_with_default_images_folder(self):
        self.test_object.execute()
        self.home_directory_copier.copy_in.assert_called_once_with(self.test_object.IMAGES_FOLDER_PATH)
