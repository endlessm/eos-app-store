import unittest
from startup.beatbox_tasks import BeatboxTasks

from mock import Mock
from mock import call
import shutil
import os
import os.path

class BeatboxTasksTest(unittest.TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._mock_home_path_provider = Mock()
        self._mock_home_path_provider.get_user_directory = Mock(return_value="")
        self._mock_os_util.execute = Mock()

        self._test_object = BeatboxTasks(self._mock_home_path_provider, self._mock_os_util)

        shutil.rmtree("/tmp/default_music", True)
        os.makedirs("/tmp/default_music")
        open("/tmp/default_music/test.music", "w").close()
        def default_music_stub():
            return "/tmp/default_music/*"
        self._test_object._default_music_directory = default_music_stub

        self._orig_copy = shutil.copy2
        self._mock_copy = Mock()
        shutil.copy2 = self._mock_copy

    def tearDown(self):
        self._clean_up()
        shutil.copy2 = self._orig_copy

    def _clean_up(self):
        shutil.rmtree("/tmp/default_music", True)

    def test_music_folder_settings_for_beatbox(self):
        music_folder = "a music folder"
        self._mock_home_path_provider.get_user_directory = Mock(return_value=music_folder)

        self._test_object.execute()

        self._mock_os_util.execute.assert_has_calls([
                call(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", music_folder])
                ])

    def test_internationalized_music_directory_is_used(self):
        self._test_object.execute()

        self._mock_home_path_provider.get_user_directory.assert_called_once_with("Music")

    def test_copy_default_musics(self):
        music_files_directory = "music_files directory"
        self._mock_home_path_provider.get_user_directory = Mock(return_value=music_files_directory)

        self._test_object.execute()

        self._mock_copy.assert_called_once_with("/tmp/default_music/test.music", os.path.join(music_files_directory, "test.music"))

    def test_default_music_directory(self):
        self.assertEquals("/usr/share/endlesm/default_music", BeatboxTasks(Mock(),Mock())._default_music_directory())
