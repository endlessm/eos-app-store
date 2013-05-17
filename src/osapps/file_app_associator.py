from os_util import OsUtil

class FileAppAssociator(object):
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util
    
    def associated_app(self, filename):
        mime_type = self._os_util.execute(["xdg-mime", "query", "filetype", filename])
        return self._os_util.execute(["xdg-mime", "query", "default", mime_type])