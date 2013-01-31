import unittest
import os

from startup.auto_updates.update_lock import UpdateLock

class UpdateLockTestCase(unittest.TestCase):
    def setUp(self):
        self._random_lock_file = "/tmp/foo"
        self._cleanUp()

    def tearDown(self):
        self._cleanUp()

    def _cleanUp(self):
        if os.path.exists(UpdateLock.LOCK_FILE):
            os.unlink(UpdateLock.LOCK_FILE)
        if os.path.exists(self._random_lock_file):
            os.unlink(self._random_lock_file)

    def test_functionality_of_the_arbitrary_lock_file(self):
        self.assertFalse(UpdateLock(self._random_lock_file).is_locked())

        self.assertTrue(UpdateLock(self._random_lock_file).acquire())
        self.assertFalse(UpdateLock(self._random_lock_file).acquire())

        self.assertTrue(UpdateLock(self._random_lock_file).is_locked())

        UpdateLock(self._random_lock_file).release()

        self.assertFalse(UpdateLock(self._random_lock_file).is_locked())

        self.assertTrue(UpdateLock(self._random_lock_file).acquire())

        self.assertTrue(UpdateLock(self._random_lock_file).is_locked())

        UpdateLock(self._random_lock_file).release()

        self.assertFalse(UpdateLock(self._random_lock_file).is_locked())

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
