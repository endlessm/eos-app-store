import gobject
import string
import gtk.keysyms
import gtk
from shortcut.desktop_shortcut import DesktopShortcut



class SeparatorShortcut(DesktopShortcut):
    __gsignals__ = {
        "application-shortcut-move": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    left = None
    right = None
    left_widget = None
    right_widget = None
    expanded = False
    _all_separators = set()
    
    def __init__(self, width=30, height=64):
        super(SeparatorShortcut, self).__init__('', draggable=False)
        # listen for motion on all widgets
        DesktopShortcut._add_motion_broadcast_callback(
            SeparatorShortcut._motion_broadcast_callback
            )
        # listen for drag end on all widgets
        DesktopShortcut._add_drag_end_broadcast_callback(
            SeparatorShortcut._drag_end_broadcast_callback
            )            
        self.w = width
        self.h = height
        self.set_size_request(self.w, self.h)
        self.class_name = 'sch_sep'
        self._event_box._sep_obj = self
        SeparatorShortcut._all_separators.add(self)
        self._image_name = ''
        self._show_background = True
        self.show_all()
        
    # DND Callbacks
    def _received_handler_callback(self, source, destination, x, y, data=None):
        if hasattr(destination, '_sep_obj'):
            source_name = source._identifier
            if destination._sep_obj.right_widget:
                destination_name = destination._sep_obj.right_widget._identifier
            else:
                destination_name = ''
        
            self.emit(
                "application-shortcut-move",
                source_name, 
                destination_name
                )
        
    @classmethod
    def _motion_broadcast_callback(cls, source, destination, x, y):
        if hasattr(destination, '_sep_obj'):
            if (y > 10) and (y < (destination._sep_obj.h-10)):
                destination._sep_obj.expand()
            else:
                SeparatorShortcut._reset_all()
        else:
            SeparatorShortcut._reset_all()
            
    @classmethod
    def _drag_end_broadcast_callback(cls, source):
        SeparatorShortcut._reset_all()
            
    @classmethod
    def _reset_all(cls):
        for sep in cls._all_separators:
            sep.reset()
        
    def SetLeftSeparator(self, separator=None):
        self.left = separator
        
    def SetLeftWidget(self, widget=None):
        self.left_widget = widget
        
    def SetRightSeparator(self, separator=None):
        self.right = separator
        
    def SetRightWidget(self, widget=None):
        self.right_widget = widget
        
    def expand(self):
        _w = 0
        if self.left:
            self.left.set_size_request(self.left.w-10, self.left.h)
            _w += 10
        if self.right:
            self.right.set_size_request(self.right.w-10, self.right.h)
            _w += 10
        self.set_size_request(self.w+_w, self.h)
        self.expanded = True
        
    def reset(self):
        if self.left:
            self.left.set_size_request(self.left.w, self.left.h)
        if self.right:
            self.right.set_size_request(self.right.w, self.right.h)
        self.set_size_request(self.w, self.h)
        self.expanded = False
        