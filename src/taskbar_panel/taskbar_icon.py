import gtk
from gtk import gdk

from util import image_util

class TaskbarIcon(gtk.EventBox):
    SELECTED_ICON_PADDING = 3
    
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
        self._is_selected = is_selected
        
        self.set_tooltip_text(window_name)
        
        if is_selected:
            overlay = self._scaled_selected_overlay.copy()
            scaled_pixbuf = pixbuf.scale_simple(pixbuf.get_width()-(self.SELECTED_ICON_PADDING*2), 
                                                pixbuf.get_height()-(self.SELECTED_ICON_PADDING*2),
                                                gdk.INTERP_BILINEAR)
            scaled_pixbuf.composite(
                                 overlay,
                                 self.SELECTED_ICON_PADDING, self.SELECTED_ICON_PADDING,
                                 scaled_pixbuf.get_width(), scaled_pixbuf.get_height(),
                                 self.SELECTED_ICON_PADDING, self.SELECTED_ICON_PADDING,
                                 1, 1,
                                 gdk.INTERP_BILINEAR,
                                 255)
            
            pixbuf = overlay
            
        self._icon.set_from_pixbuf(pixbuf)
