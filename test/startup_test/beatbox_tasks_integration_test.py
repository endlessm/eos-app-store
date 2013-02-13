import unittest
from startup.beatbox_tasks import BeatboxTasks
from mock import Mock
import shutil
import os
from startup.home_directory_file_copier import HomeDirectoryFileCopier
from osapps.os_util import OsUtil

class BeatboxIntegrationTaskTest(unittest.TestCase):
    def setUp(self):
        self._destination = '/tmp/destination'
        self._source = '/tmp/default_music'

        shutil.rmtree(self._source, True)
        shutil.rmtree(self._destination, True)
        os.makedirs("/tmp/default_music")
        open("/tmp/default_music/test.music", "w").close()
        open("/tmp/default_music/test2.music", "w").close()

        os.makedirs(self._destination)

        self.home_path_provider = Mock()
        self.home_path_provider.get_user_directory = Mock(return_value=self._destination)
        self.home_directory_copier = HomeDirectoryFileCopier(self.home_path_provider)
        self.os_util = Mock()

        self.test_object = BeatboxTasks(self.home_directory_copier, self.home_path_provider, self.os_util)

    def tearDown(self):
        shutil.rmtree(self._source, True)
        shutil.rmtree(self._destination, True)

    def test_copying_music_folders(self):
        self.test_object.SOURCE_DIR = '/tmp/default_music'
        self.test_object.execute()

        self.assertTrue(os.path.isfile("/tmp/destination/test.music"))
        self.assertTrue(os.path.isfile("/tmp/destination/test2.music"))

