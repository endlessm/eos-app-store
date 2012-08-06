import gtk

class TaskbarIcon(gtk.EventBox):
    def __init__(self, task, name, pixbuf, is_selected):
        super(TaskbarIcon, self).__init__()
        
        self._task = task
        self._name = name
        self.set_visible_window(is_selected)
        self._icon = gtk.Image()
        self._icon.set_from_pixbuf(pixbuf)
        self.set_tooltip_text(name)
        
        icon_holder = gtk.Alignment(0.5, 0.5, 0, 0)
        icon_holder.set_padding(2, 2, 0, 0)
        icon_holder.add(self._icon)
        
        self.add(icon_holder)
        
    def task(self):
        return self._task

