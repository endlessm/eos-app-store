import os

class TaskbarShortcut():
    def is_launcher_present(self, path):
        return os.path.isfile(path)
            
    
    
