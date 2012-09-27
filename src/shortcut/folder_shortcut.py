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
        super(FolderShortcut, self).__init__(shortcut.name())
        
        self._callback = callback
        
        self._shortcut = shortcut
        self._normal_text = shortcut.name()
        
        self._event_box.connect("button-press-event", self.mouse_press_callback)

        self.show_all()
        
    # DND Callbacks
    def _transmiter_handler_callback(self, source):
        print 
        print '-> FolderShortcut::_transmiter_handler_callback'
        print '    source', source
        return 'some random data'
     
    def _received_handler_callback(self, source, destination, x, y, data=None):
        print 
        print '-> FolderShortcut::_received_handler_callback'
        print '    source', source
        print '    tdestination', destination
        print '    x:%s, y:%s' % (x, y)
        print '    data', data
        
    def mouse_press_callback(self, widget, event):
        if event.button == 1:# and event.type == gtk.gdk._2BUTTON_PRESS:
            self._callback(widget, event, self._shortcut)
            # must propagate for DND to work
            #return True
        return False
    
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
    
    def get_images(self):
        return (image_util.image_path("endless-shortcut-well.png"),image_util.image_path("folder.png"),image_util.image_path("endless-shortcut-foreground.png"))
