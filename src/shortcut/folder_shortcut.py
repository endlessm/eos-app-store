from shortcut.desktop_shortcut import DesktopShortcut
from shortcut.application_shortcut import ApplicationShortcut
from util import image_util
import gtk
import gobject

class FolderShortcut(DesktopShortcut):
    __gsignals__ = {
        "folder-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)),
        "folder-shortcut-relocation": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, shortcut, callback):
        super(FolderShortcut, self).__init__(shortcut.name())
        
        self._callback = callback
        
        self._shortcut = shortcut
        self._normal_text = shortcut.name()
        
        self._event_box.connect("button-release-event", self.mouse_release_callback)
        
        DesktopShortcut._add_drag_end_broadcast_callback(
            self._drag_end_broadcast_callback
            )

        self.show_all()
        self.set_moving(False)
        
    def _received_handler_callback(self, source, destination, x, y, data=None):
        if isinstance(source.parent, ApplicationShortcut):
            source_name = source._identifier
            destination_name = destination._identifier
            self.emit(
                "folder-shortcut-relocation",
                source_name, 
                destination_name
                )
                
    def _drag_enter_handler_callback(self, source, destination):
        if isinstance(source.parent, ApplicationShortcut):
            self._event_box.set_images(self.get_images_hover())
            self.hide()
            self.show()
            
    def _drag_leave_handler_callback(self, source, destination):
        self._event_box.set_images(self.get_images())
        self.hide()
        self.show()
            
    def _drag_end_broadcast_callback(self, source):
        self._event_box.set_images(self.get_images())
        self.hide()
        self.show()

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
        return (
            image_util.image_path("endless-shortcut-well.png"), 
            image_util.image_path("folder.png"), 
            image_util.image_path("endless-shortcut-foreground.png")
            )
        
    def get_images_hover(self):
        return (
            image_util.image_path("icon_highlight.png"), 
            image_util.image_path("folder.png"), 
            image_util.image_path("endless-shortcut-foreground.png")
            )
