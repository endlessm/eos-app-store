import unittest
from startup.beatbox_tasks import BeatboxTasks
from mock import Mock
import shutil
import os
from osapps.os_util import OsUtil
from osapps.home_path_provider import HomePathProvider

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

        home_path_provider = HomePathProvider()
        home_path_provider.PREFIX = self._destination
        self.test_object = BeatboxTasks(home_path_provider=home_path_provider, os_util=Mock())

    def tearDown(self):
        shutil.rmtree(self._source, True)
        shutil.rmtree(self._destination, True)

    def test_copying_music_folders(self):
        self.test_object.SOURCE_DIR = '/tmp/default_music'
        self.test_object.execute()

        self.assertTrue(os.path.isfile("/tmp/destination/Music/Endless/test.music"))
        self.assertTrue(os.path.isfile("/tmp/destination/Music/Endless/test2.music"))

