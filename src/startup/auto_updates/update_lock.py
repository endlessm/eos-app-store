import os

class UpdateLock():
    LOCK_FILE = "/tmp/endless_update.lock"
    
    def __init__(self, filename=LOCK_FILE):
        self._lock_filename = filename

    def acquire(self):
        if self.is_locked():
            return False

        open(self._lock_filename, "w").close()
        return True

    def release(self):
        if os.path.isfile(self._lock_filename):
            os.unlink(self._lock_filename)

    def is_locked(self):
        return os.path.isfile(self._lock_filename)
