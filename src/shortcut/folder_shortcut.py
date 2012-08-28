from shortcut.desktop_shortcut import DesktopShortcut
from util import image_util
import gtk
import gobject

class FolderShortcut(DesktopShortcut):
    __gsignals__ = {
        "application-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, shortcut, callback):
        self._shortcut = shortcut
        self._normal_text = shortcut.name()

        super(FolderShortcut, self).__init__(shortcut.name())
        
        self._callback = callback
        
        self._event_box.connect("button-release-event", self.mouse_press_callback)

        self.show_all()
        
    def mouse_press_callback(self, widget, event):
        if event.button == 1:# and event.type == gtk.gdk._2BUTTON_PRESS:
            self._callback(widget, event, self._shortcut)
            return True
        return False
    
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
    
    def get_images(self):
        image_name = self._shortcut.icon()
        if not image_name:
            image_name = image_util.image_path("folder.png")
        return (image_util.image_path("endless-shortcut-well.png"), image_name, image_util.image_path("endless-shortcut-foreground.png"))
