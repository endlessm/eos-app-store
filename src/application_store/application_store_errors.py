class ApplicationStoreError(Exception):
    def __init__(self, msg = ''):
        self._msg = msg
    
    def __str__(self):
        return (repr(self._msg))

class ApplicationStoreWrappedException(ApplicationStoreError):
    def __init__(self, original_exception, msg = ''):
        super(ApplicationStoreWrappedException, self).__init__(msg)
        self._original_exception = original_exception
    
    def __str__(self):
        return (super(ApplicationStoreWrappedException, self).__str__(), repr(self._original_exception), repr(self._original_exception.__str__()))