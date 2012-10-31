from threading import Thread
from startup.update_checker import UpdateChecker
import time

class UpdateManager(object):
    SLEEP_TIME = 60 * 60 * 24
    
    def __init__(self, update_checker=UpdateChecker()):
        self._update_checker = update_checker
    
    def execute(self):
        self._done = False
        self._running_thread = Thread(target=self._background_process)
        self._running_thread.start()
        
    def _background_process(self):
        while not self._done:
            self._update_checker.check_for_updates()
            time.sleep(self.SLEEP_TIME) 