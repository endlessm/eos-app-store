from threading import Thread
import time

from eos_log import log
from startup.auto_updates.update_checker import UpdateChecker

class UpdateManager(object):
    SLEEP_TIME = 60 * 60
    
    def __init__(self, update_checker=UpdateChecker()):
        self._update_checker = update_checker
    
    def execute(self):
        self._done = False
        self._running_thread = Thread(target=self._background_process)
        self._running_thread.start()
        
    def _background_process(self):
        while not self._done:
            try:
                self._update_checker.check_for_updates()
            except(Exception) as e:
                log.error("An error occurred during the check for updates", e)
            time.sleep(self.SLEEP_TIME) 
