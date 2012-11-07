import unittest
from startup.beatbox_tasks import BeatboxTasks
from mock import Mock

class BeatboxTaskTest(unittest.TestCase):
    def setUp(self):
        self.home_directory_copier = Mock()
        self.os_util = Mock()
        self.os_util.execute = Mock()
        self.home_path = "home_path"
        self.home_path_provider = Mock(return_value=self.home_path)

        self.test_object = BeatboxTasks(self.home_path_provider,self.home_directory_copier, self.os_util)

    def test_default_location_is_correct(self):
        self.assertEquals("/usr/share/endlessm/default_music",
                self.test_object._default_music_folder_path())

    def test_gsettings_are_set_for_beatbox(self):
        self.test_object.execute()
        self.os_util.execute.assert_called_once_with(["gsettings",
            "set", "net.launchpad.beatbox.settings", "music-folder",
            self.home_path])

    def test_target_dir_is_correct(self):
        self.assertEqual('Music', self.test_object.TARGET_DIR)

    def test_file_copier_is_called_with_default_music_folder(self):
        self.test_object.execute()
        self.home_directory_copier.copy_from.assert_called_once_with(self.test_object._default_music_folder_path())
