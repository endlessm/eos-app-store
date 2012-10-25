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

    _motion_callbacks = []
    _drag_end_callbacks = []
    _drag_begin_callbacks = []
    @classmethod
    def _add_motion_broadcast_callback(cls, callback):
        cls._motion_callbacks.append(callback)
        
    @classmethod
    def _add_drag_end_broadcast_callback(cls, callback):
        cls._drag_end_callbacks.append(callback)
        
    @classmethod
    def _add_drag_begin_broadcast_callback(cls, callback):
        cls._drag_begin_callbacks.append(callback)
    
    @classmethod
    def _motion_broadcast(cls, source, destination, x, y):
        for cb in cls._motion_callbacks:
            cb(source, destination, x, y)
            
    @classmethod
    def _drag_end_broadcast(cls, source):
        for cb in cls._drag_end_callbacks:
            cb(source)
    
    @classmethod
    def _drag_begin_broadcast(cls, source):
        for cb in cls._drag_begin_callbacks:
            cb(source)
        
    def __init__(self, label_text="", draggable=True):
        super(DesktopShortcut, self).__init__()
        self.set_size_request(64, 64)
        self._event_box = self._create_icon(self.get_images(self.ICON_STATE_NORMAL))
        
        self._label = gtk.Label(label_text)
        self._identifier = label_text
        self._event_box._identifier = label_text

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

        if draggable:
            self._event_box.connect("drag_data_get", self.dnd_send_data)
            self._event_box.drag_source_set(
                gtk.gdk.BUTTON1_MASK, 
                self.DND_TRANSFER_TYPE, 
                gtk.gdk.ACTION_MOVE
                )
        self._event_box.connect("drag_data_received", self.dnd_receive_data)
        self._event_box.connect("drag_motion", self.dnd_motion_data)
        self._event_box.connect("drag_end", self.dnd_drag_end)
        self._event_box.connect("drag_begin", self.dnd_drag_begin)
        self._event_box.drag_dest_set(
            #gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_DROP,
            self.DND_TRANSFER_TYPE, 
            gtk.gdk.ACTION_MOVE
            )
        
    def dnd_send_data(self, widget, context, selection, targetType, eventTime):
        if targetType == self.DND_TARGET_TYPE_TEXT:
            if hasattr(self, '_transmiter_handler_callback'):
                data = self._transmiter_handler_callback(widget)
                selection.set(selection.target, 8, data)
            else:
                selection.set(selection.target, 8, self._identifier)
        
    def dnd_receive_data(self, widget, context, x, y, selection, targetType, time):
        source_widget = context.get_source_widget()
        if targetType == self.DND_TARGET_TYPE_TEXT:
            if hasattr(self, '_received_handler_callback'):
                self._received_handler_callback(
                    source_widget, 
                    widget, 
                    x, 
                    y, 
                    selection.data
                    )
            
    def dnd_motion_data(self, widget, context, x, y, time):
        source_widget = context.get_source_widget()
        DesktopShortcut._motion_broadcast(source_widget, widget, x, y)
        if hasattr(self, '_motion_handler_callback'):
            self._motion_handler_callback(source_widget, widget, x, y)
        context.drag_status(gtk.gdk.ACTION_MOVE, time)
        return True
        
    def dnd_drag_end(self, widget, context):
        self._label.show()
        self._event_box.show()
        self.set_moving(False)
        DesktopShortcut._drag_end_broadcast(widget)
        
    def dnd_drag_begin(self, widget, context):
        self._label.hide()
        self._event_box.hide()
        self.set_moving(True)
        DesktopShortcut._drag_begin_broadcast(widget)
   
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

