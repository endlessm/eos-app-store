import unittest
from startup.beatbox_tasks import BeatboxTasks

from mock import Mock
from mock import call
import shutil
import os
import os.path


class BeatboxTaskTest(unittest.TestCase):
    def setUp(self):
        home_directory_copier = Mock()
        self.os_util = Mock()
        self.os_util.execute = Mock()
        self.task = BeatboxTasks(home_directory_copier, self.os_util)

    def test_gsettings_are_set_for_beatbox(self):
        self.task.execute()
        self.os_util.execute.assert_called_once_with(["gsettings", "set", "net.launchpad.beatbox.settings", "music-folder", "/usr/share/endlessm/default_music"])
