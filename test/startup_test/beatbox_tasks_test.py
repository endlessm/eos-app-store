import unittest
from startup.beatbox_tasks import BeatboxTasks
from mock import Mock

class BeatboxTaskTest(unittest.TestCase):
    def setUp(self):
        mock_manager = Mock()
        self._home_directory_copier = mock_manager.home_directory_copier
        self._os_util = mock_manager.os_util
        self._home_path_provider = mock_manager.home_path_provider

        self.test_object = BeatboxTasks(self._home_directory_copier, self._home_path_provider, self._os_util)

    def test_gsettings_are_set_for_beatbox(self):
        user_directory = "this is the user directory"
        self._home_path_provider.get_user_directory = Mock(return_value=user_directory)

        self.test_object.execute()
        self._os_util.execute.assert_called_once_with(["gsettings", "set", "net.launchpad.beatbox.Settings", "music-folder", user_directory])

    def test_source_and_target_dir_are_correct(self):
        self.assertEqual("Music/Endless", self.test_object.TARGET_DIR)
        self.assertEquals("/usr/share/endlessm-default-files/default_music", self.test_object.SOURCE_DIR)

    def test_file_copier_is_called_with_default_music_folder(self):
        self.test_object.execute()
        self._home_directory_copier.copy.assert_called_once_with(self.test_object.SOURCE_DIR, self.test_object.TARGET_DIR)
