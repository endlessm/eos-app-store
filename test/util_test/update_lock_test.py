import unittest
import os

from util.update_lock import UpdateLock

class UpdateLockTestCase(unittest.TestCase):
    def setup(self):
        self._cleanUp()

    def tearDown(self):
        self._cleanUp()

    def _cleanUp(self):
        if os.path.exists(UpdateLock.LOCK_FILE):
            os.unlink(UpdateLock.LOCK_FILE)

    def test_functionality_of_the_lock_file(self):
        self.assertFalse(UpdateLock().is_locked())

        self.assertTrue(UpdateLock().acquire())
        self.assertFalse(UpdateLock().acquire())

        self.assertTrue(UpdateLock().is_locked())

        UpdateLock().release()

        self.assertFalse(UpdateLock().is_locked())

        self.assertTrue(UpdateLock().acquire())

        self.assertTrue(UpdateLock().is_locked())

        UpdateLock().release()

        self.assertFalse(UpdateLock().is_locked())
