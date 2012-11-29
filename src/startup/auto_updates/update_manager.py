from threading import Thread
import time

from eos_log import log
from startup.auto_updates.update_checker import UpdateChecker
from startup.auto_updates.update_lock import UpdateLock

class UpdateManager(object):
    SLEEP_TIME = 60 * 60 # One hour
    
    def __init__(self, update_checker=UpdateChecker()):
        self._update_checker = update_checker

        self._lock = UpdateLock()
        self._lock.release()
    
    def execute(self):
        self._done = False
        self._running_thread = Thread(target=self._background_process)
        self._running_thread.setDaemon(True)
        self._running_thread.start()
        
    def _background_process(self):
        while not self._done:
            self.update_os()
            time.sleep(self.SLEEP_TIME) 
            
    def update_os(self):
        log.info("attempting to acquire update lock")
        if self._lock.acquire():
            try:
                self._update_checker.check_for_updates()
            except(Exception) as e:
                log.error("An error occurred during the check for updates", e)
            self._lock.release()
        else:
            log.info("failed to acquire update lock")
