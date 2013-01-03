import os

class TaskbarShortcut():
    def __init__(self, displayed_shortcut, path):
        self.path = path
        self.displayed_shortcut = displayed_shortcut
        
    def display(self, canvas):
        if os.path.isfile(self.path):
            canvas(self.displayed_shortcut)
    
    
