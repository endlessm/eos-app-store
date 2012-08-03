import gtk

class TaskbarIcon(gtk.EventBox):
    def __init__(self, task, name, pixbuf):
        super(TaskbarIcon, self).__init__()
        self._task = task
        self._name = name
        self.set_visible_window(False)
        self._icon = gtk.Image()
        self._icon.set_from_pixbuf(pixbuf)
        self.add(self._icon)
        
    def task(self):
        return self._task

