import unittest
from startup.beatbox_tasks import BeatboxTasks

from mock import Mock
from mock import call
import shutil
import os
import os.path


class BeatboxTaskTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/originating")
        open("/tmp/originating/test.music", "w").close()
        open("/tmp/originating/test2.music", "w").close()
        os.makedirs("/tmp/destination")

        home_path_provider = Mock()
        home_path_provider.get_user_directory = Mock(return_value="/tmp/destination")
        os_util = Mock()
        os_util.execute = Mock()
        self.task = BeatboxTasks("/tmp/originating/*", home_path_provider, os_util)

    def tearDown(self):
        shutil.rmtree("/tmp/originating", True)
        shutil.rmtree("/tmp/destination", True)

    def test_copying_files(self):
        self.task.execute()
        self.assertTrue(os.path.isfile("/tmp/destination/test.music"))
        self.assertTrue(os.path.isfile("/tmp/destination/test2.music"))
