class ApplicationStoreError(Exception):
    def __init__(self, original_exception, msg = ''):
        self._original_exception = original_exception
        self._msg = msg
    
    def __str__(self):
        return repr(self._original_exception)
        