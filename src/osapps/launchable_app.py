class LaunchableApp(object):
    def __init__(self, executable, desktop):
        self._executable = executable
        self._desktop = desktop
        
    def desktop(self):
        return self._desktop
    
    def executable(self):
        return self._executable
    
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self._desktop == other._desktop)

    def __ne__(self, other):
        return not self.__eq__(other)
