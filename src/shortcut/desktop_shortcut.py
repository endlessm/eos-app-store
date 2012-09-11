import string
from util import label_util
import gobject
from util.image_eventbox import ImageEventBox
import gtk

class DesktopShortcut(gtk.VBox):
    DND_TARGET_TYPE_TEXT = 80
    DND_TRANSFER_TYPE = [( "text/plain", gtk.TARGET_SAME_APP, DND_TARGET_TYPE_TEXT )]
    ICON_STATE_NORMAL = 'normal'
    ICON_STATE_PRESSED = 'pressed'
    ICON_STATE_MOUSEOVER = 'mouseover'
    
    
    __gsignals__ = {
           "application-shortcut-dragging-over": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                                                  gobject.TYPE_NONE,
                                                  (gobject.TYPE_PYOBJECT,)), 
    }
    
    def __init__(self, label_text=""):
        super(DesktopShortcut, self).__init__()
        self.set_size_request(64, 64)
        
#        self._event_box = self._create_event_box() 
#        self._icon = self._create_icon(self.get_images())
#        self._event_box.add(self._icon)
        self._event_box = self._create_icon(self.get_images(self.ICON_STATE_NORMAL))
        
        self._label = gtk.Label(label_text)

        new_style = self._label.get_style().copy()
        new_style.fg[gtk.STATE_NORMAL] = self._label.get_colormap().alloc('#f0f0f0')
        self._label.set_style(new_style)
        
        text = string.strip(label_text) 
        self._label.set_text(label_util.wrap_text(self._label, text))
        
        self._label.set_alignment(0.5, 0.0)
        
        self._label_event_box = gtk.EventBox()
        self._label_event_box.add(self._label)
        self._label_event_box.set_visible_window(False)
        
        self.pack_start(self._event_box, False, False, 3)
        self.pack_start(self._label_event_box, False, False, 3)
        
        self._event_box.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                                     self.DND_TRANSFER_TYPE, 
                                     gtk.gdk.ACTION_MOVE)
   
    def set_moving(self, is_moving):
        self._is_moving = is_moving
        
    def is_moving(self):
        return self._is_moving
    
    def get_shortcut(self):
        return None
    
    def get_images(self, event_state):
        return ()
    
    def remove_shortcut(self):
        if self.parent != None:
            self.parent.remove(self)
            
            for callback in self._callbacks:
                self.disconnect_by_func(callback)

            self._callbacks = []
            
    def connect(self, signal, callback):
        if not hasattr(self, "_callbacks"):
            self._callbacks = []
            
        super(DesktopShortcut, self).connect(signal, callback)
        self._callbacks.append(callback)
    
    def _create_event_box(self):
        event_box = gtk.EventBox()
        event_box.set_size_request(64,64)
        event_box.set_visible_window(False)
        event_box.show()
                
        return event_box
    
    def _create_icon(self, images):
        icon = ImageEventBox(images)
        icon.set_size_request(64,64)
        icon.set_visible_window(False)
        icon.show()
        
        return icon       
