import os

class DeleteDesktopStateTask:
    def __init__(self, os_util=os):
        self._os_util = os_util
        
    def execute(self):
        self._os_util.remove(os.path.expanduser("~/.endlessm/desktop.json"))
