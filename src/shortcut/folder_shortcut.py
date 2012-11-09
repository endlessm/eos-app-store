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
        self._shortcut = shortcut
        self._normal_text = shortcut.name()
        super(FolderShortcut, self).__init__(shortcut.name())
#        self._image = image
#        print hasattr(self, '_image')
#        print hasattr(shortcut, '_image')
        self._callback = callback
        
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
    
    def get_images(self, event_state):
        shortcut_icon_dict = self._shortcut.icon()
        default_icon = shortcut_icon_dict.get(self.ICON_STATE_NORMAL, image_util.image_path("folder.png"))
        return (shortcut_icon_dict.get(event_state, default_icon), )
        
    def get_highlight_images(self, event_state):
        icon = self.get_images(event_state)
        highlight_icon = image_util.image_path("icon_highlight.png")
        return icon + (highlight_icon, )
