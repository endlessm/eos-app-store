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
        super(FolderShortcut, self).__init__(shortcut.name())
        
        self._callback = callback
        
        self._shortcut = shortcut
        self._normal_text = shortcut.name()
        
        self._event_box.connect("button-press-event", self.mouse_press_callback)
        self._event_box.connect("button-release-event", self.mouse_release_callback)

        self.show_all()
        self.set_moving(False)
        
    # DND Callbacks    
    def _received_handler_callback(self, source, destination, x, y, data=None):
        print 
        print '-> FolderShortcut::_received_handler_callback'
        print '    source', source
        print '    tdestination', destination
        print '    x:%s, y:%s' % (x, y)
        print '    data', data
        
    def mouse_press_callback(self, widget, event):
        if event.button == 1:# and event.type == gtk.gdk._2BUTTON_PRESS:
            #self._callback(widget, event, self._shortcut)
            pass
            # must propagate for DND to work
            #return True
        return False
        
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
        return (image_util.image_path("endless-shortcut-well.png"),image_util.image_path("folder.png"),image_util.image_path("endless-shortcut-foreground.png"))
