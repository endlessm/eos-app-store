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

    def __init__(self, shortcut, callback):
        self._shortcut = shortcut
        self._normal_text = shortcut.name()

        super(FolderShortcut, self).__init__(shortcut.name())
        
        self._callback = callback
        
        self._event_box.connect("button-release-event", self.mouse_release_callback)
        self._event_box.connect("button-press-event", self.mouse_press_callback)
        self._event_box.connect("enter-notify-event", self.mouse_over_callback)
        self._event_box.connect("leave-notify-event", self.mouse_out_callback)

        self.show_all()
        self.set_moving(False)
        
    def mouse_release_callback(self, widget, event):
        if not self.is_moving():
            if event.button == 1:
                self.emit("folder-shortcut-activate", event, self._shortcut)
                self._event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
                self._event_box.hide()
                self._event_box.show()
                return True
        return False
    
    def mouse_press_callback(self, widget, event):
        if event.button == 1:
            self._event_box.set_images(self.get_images(self.ICON_STATE_PRESSED))
            self._event_box.hide()
            self._event_box.show()
            return True
        return False

    def mouse_out_callback(self, widget, event):
        self._event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
        self._event_box.hide()
        self._event_box.show()
        return True
        
    def mouse_over_callback(self, widget, event):
        self._event_box.set_images(self.get_images(self.ICON_STATE_MOUSEOVER))
        self._event_box.hide()
        self._event_box.show()
        return True

    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
    
    def get_images(self, event_state):
        shortcut_icon_dict = self._shortcut.icon()
        default_icon = shortcut_icon_dict.get(self.ICON_STATE_NORMAL, image_util.image_path("folder.png"))
        image_name = shortcut_icon_dict.get(event_state, default_icon)
        return (image_name, )
