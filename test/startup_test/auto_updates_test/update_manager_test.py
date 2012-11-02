import unittest
from mock import Mock #@UnresolvedImport

import time
from startup.auto_updates.update_manager import UpdateManager

class UpdateManagerTestCase(unittest.TestCase):
    _mock_check_for_updates_calls = 0
    
    def setUp(self):
        self._mock_update_checker = Mock()
        def side_effect(*args):
            self._mock_check_for_updates_calls += 1
        self._mock_update_checker.check_for_updates = Mock(side_effect=side_effect)
        
        self._test_object = UpdateManager(self._mock_update_checker)
    
    def test_execute_starts_up_thread(self):
        self._test_object.SLEEP_TIME = 1
        self._test_object.execute()
        time.sleep(1)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
        self.assertTrue(self._mock_check_for_updates_calls > 0)