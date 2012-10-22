import unittest
from startup.beatbox_tasks import BeatboxTasks

class BeatboxTasksTest(unittest.TestCase):
    def setUp(self):
        self._test_object = BeatboxTasks()
    
    def test_(self):
        self._test_object.execute()