from shortcut.desktop_shortcut import DesktopShortcut
from util import image_util
import gtk
import gobject

class FolderShortcut(DesktopShortcut):
    __gsignals__ = {
        "folder-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, shortcut, callback, image=''):
        self.image = image
        self._shortcut = shortcut
        super(FolderShortcut, self).__init__(shortcut.name())
#        self._image = image
#        print hasattr(self, '_image')
#        print hasattr(shortcut, '_image')
        self._callback = callback
        
        
        self._shortcut._image = image
        self._normal_text = shortcut.name()
        
        self._event_box.connect("button-release-event", self.mouse_release_callback)

        self.show_all()
        self.set_moving(False)
        
    def mouse_release_callback(self, widget, event):
        if not self.is_moving():
            if event.button == 1:
                self.emit("folder-shortcut-activate", event, self._shortcut)
                self._event_box.set_images(self.get_images())
                self._event_box.hide()
                self._event_box.show()
                return True
        return False
    
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
    
    def get_images(self):
        image = self.image or image_util.image_path("folder.png")
        return (image_util.image_path("endless-shortcut-well.png"), image ,image_util.image_path("endless-shortcut-foreground.png"))
