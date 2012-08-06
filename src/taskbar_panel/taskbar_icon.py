import gtk
from gtk import gdk

from util import image_util

class TaskbarIcon(gtk.EventBox):
    def __init__(self, task, name, pixbuf, is_selected):
        selected_overlay = image_util.load_pixbuf('endless-shortcut-well.png')
        self._scaled_selected_overlay = selected_overlay.scale_simple(pixbuf.get_width(), pixbuf.get_height(), gdk.INTERP_BILINEAR) 
        
        super(TaskbarIcon, self).__init__()
        self.set_visible_window(False)
        
        self._task = task
        self._name = name
        self._is_selected = is_selected

        self._icon = gtk.Image()
        
        self.update_task(name, pixbuf, is_selected)
        
        icon_holder = gtk.Alignment(0.5, 0.5, 0, 0)
        icon_holder.set_padding(2, 2, 3, 3)
        icon_holder.add(self._icon)
        
        self.add(icon_holder)
        
    def task(self):
        return self._task

    def is_selected(self):
        return self._is_selected

    def update_task(self, window_name, pixbuf, is_selected):
        self.set_tooltip_text(window_name)
        overlay = self._scaled_selected_overlay.copy()
        if is_selected:
            pixbuf.composite(
                                 overlay,
                                 0, 0,
                                 pixbuf.get_width(), pixbuf.get_height(),
                                 2, 2,
                                 0.8, 0.8,
                                 gdk.INTERP_BILINEAR,
                                 255)
            
            del pixbuf
            pixbuf = overlay
            
        self._icon.set_from_pixbuf(pixbuf)
