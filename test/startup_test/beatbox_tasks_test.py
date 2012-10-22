import unittest
from startup.beatbox_tasks import BeatboxTasks

from mock import Mock
from mock import call

class BeatboxTasksTest(unittest.TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._mock_home_path_provider = Mock()
        
        self._test_object = BeatboxTasks(self._mock_home_path_provider, self._mock_os_util)
    
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
