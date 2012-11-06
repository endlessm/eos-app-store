import unittest
from mock import Mock #@UnresolvedImport
import time

from eos_log import log
from startup.auto_updates.update_manager import UpdateManager

class UpdateManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_update_checker = Mock()
        
        self._test_object = UpdateManager(self._mock_update_checker)
        self._mock_check_for_updates_calls = 0
        self._orig_eos_error = log.error
        log.error = Mock()

    def tearDown(self):
        log.error = self._orig_eos_error 
    
    def test_execute_starts_up_thread(self):
        def side_effect():
            self._mock_check_for_updates_calls += 1
        self._mock_update_checker.check_for_updates = Mock(side_effect=side_effect)

        self._test_object.SLEEP_TIME = 0
        self._test_object.execute()
        time.sleep(.1)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
        self.assertTrue(self._mock_check_for_updates_calls > 0, 
                "should have called the check for updates at least once")

    def test_thread_continues_to_live_regardless_of_exception_thrown_during_check_for_updates(self):
        def side_effect():
            self._mock_check_for_updates_calls += 1
            if self._mock_check_for_updates_calls == 1:
                raise Exception()
        self._mock_update_checker.check_for_updates = Mock(side_effect=side_effect)

        self._test_object.SLEEP_TIME = 0
        self._test_object.execute()
        time.sleep(.2)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
        self.assertTrue(self._mock_check_for_updates_calls > 1,
                "should have called the check for updates at least twice")

    def test_log_exception(self):
        exception = Exception("something bad happened")

        def side_effect():
            self._mock_check_for_updates_calls += 1
            if self._mock_check_for_updates_calls == 1:
                raise exception
        self._mock_update_checker.check_for_updates = Mock(side_effect=side_effect)

        self._test_object.SLEEP_TIME = 0
        self._test_object.execute()
        time.sleep(.1)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
        log.error.assert_called_once_with("An error occurred during the check for updates", exception)

