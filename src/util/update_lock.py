import os

class UpdateLock():
    LOCK_FILE = "/tmp/endless_update.lock"

    def acquire(self):
        if self.is_locked():
            return False

        open(self.LOCK_FILE, "w").close()
        return True

    def release(self):
        if os.path.exists(self.LOCK_FILE):
            os.unlink(self.LOCK_FILE)

    def is_locked(self):
        return os.path.exists(self.LOCK_FILE)
