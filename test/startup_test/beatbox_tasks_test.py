import unittest
from startup.beatbox_tasks import BeatboxTasks
from mock import Mock, call

class BeatboxTaskTest(unittest.TestCase):
    def setUp(self):
        self._mock_manager = Mock()
        self._copier = self._mock_manager.copier
        self._os_util = self._mock_manager.os_util
        self._home_path_provider = self._mock_manager.home_path_provider

        self.test_object = BeatboxTasks(self._copier, self._home_path_provider, self._os_util)

    def test_gsettings_are_set_for_beatbox(self):
        user_directory = "this is the user directory"
        self._home_path_provider.get_music_directory = Mock(return_value=user_directory)

        self.test_object.execute()

        self._os_util.execute.assert_called_once_with(["gsettings", "set", "net.launchpad.beatbox.Settings", "music-folder", user_directory])

    def test_source_and_target_dir_are_correct(self):
        self.assertEqual("Endless", self.test_object.TARGET_DIR)
        self.assertEquals("/usr/share/endlessm-default-files/default_music", self.test_object.SOURCE_DIR)

    def test_file_copier_is_called_with_default_music_folder(self):
        music_directory = "this is the music directory"
        self._home_path_provider.get_music_directory = Mock(return_value=music_directory)
        self.test_object.execute()

        self._copier.assert_called_once_with(self.test_object.SOURCE_DIR, music_directory)

    def test_music_path_has_endless_subfolder(self):
        expected_call = call.home_path_provider.get_music_directory(self.test_object.TARGET_DIR)

        self.test_object.execute()

        self.assertTrue(expected_call in self._mock_manager.mock_calls)
