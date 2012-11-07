import unittest
from mock import Mock #@UnresolvedImport
import time
import os

from eos_log import log
from startup.auto_updates.update_manager import UpdateManager
from util.update_lock import UpdateLock

class UpdateManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_update_checker = Mock()
        
        self._test_object = UpdateManager(self._mock_update_checker)
        self._mock_check_for_updates_calls = 0
        self._orig_eos_error = log.error
        log.error = Mock()

        self._cleanUp()

    def tearDown(self):
        log.error = self._orig_eos_error 

        self._cleanUp()

    def _cleanUp(self):
        UpdateLock().release()
    
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

    def test_dont_check_for_udates_if_update_lock_is_locked(self):
        assert UpdateLock().acquire()

        self._mock_update_checker.check_for_updates = Mock()

        self._test_object.SLEEP_TIME = 0
        self._test_object.execute()
        time.sleep(.1)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
        self.assertFalse(self._mock_update_checker.check_for_updates.called)

    def test_lock_the_update_lock_when_checking_for_updates(self):
        def side_effect():
            assert UpdateLock().is_locked()
        self._mock_update_checker.check_for_updates = Mock(side_effect=side_effect)

        self._test_object.SLEEP_TIME = 0
        self._test_object.execute()
        time.sleep(.1)
        self._test_object._done = True
        self._test_object._running_thread.join()
        
    def test_if_update_lock_file_exists_delete_it(self):
        open(UpdateLock.LOCK_FILE, "w").close()

        UpdateManager(self._mock_update_checker)

        self.assertFalse(os.path.exists(UpdateLock.LOCK_FILE))

    def test_update_os_checks_for_updates(self):
        self._mock_update_checker.check_for_updates = Mock()

        self._test_object.update_os()

        self.assertTrue(self._mock_update_checker.check_for_updates.called)

    def test_update_os_does_not_check_for_updates_if_update_lock_is_locked(self):
        UpdateLock().acquire()
        self._mock_update_checker.check_for_updates = Mock()

        self._test_object.update_os()

        self.assertFalse(self._mock_update_checker.check_for_updates.called)

    def test_update_os_acquires_lock_then_releases_it(self):
        self._is_update_locked = False
        def checker():
            self._is_update_locked = UpdateLock().is_locked()
        self._mock_update_checker.check_for_updates = Mock(side_effect=checker)

        self._test_object.update_os()

        self.assertTrue(self._is_update_locked)
        self.assertFalse(UpdateLock().is_locked())
        
