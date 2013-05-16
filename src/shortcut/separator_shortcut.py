from gi.repository import GObject
from shortcut.desktop_shortcut import DesktopShortcut

class SeparatorShortcut(DesktopShortcut):
    __gsignals__ = {
        "application-shortcut-move": (
            GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            GObject.TYPE_NONE,
                (
                    GObject.TYPE_PYOBJECT,
                    GObject.TYPE_PYOBJECT,
                    GObject.TYPE_PYOBJECT
                    )
            ),
        }

    left = None
    right = None
    left_widget = None
    right_widget = None
    
    def __init__(self, width, height):
        super(SeparatorShortcut, self).__init__('', draggable=False, has_icon=False,
                                                width=width, height=height)
        self.w = width
        self.h = height
        self._image_name = ''
        self._show_background = True
        self.show_all()
        
        DesktopShortcut._add_drag_end_broadcast_callback(self, self._drag_end_broadcast_callback)
        
    def _received_handler_callback(self, source, destination, x, y, data=None):
        dest_widget = destination.parent.parent
        source_widget = source.parent.parent
        
        if isinstance(dest_widget, SeparatorShortcut) and \
            (source_widget is not self.left_widget) and \
            (source_widget is not self.right_widget):
                source_shortcut = source_widget.get_shortcut()
                if source_shortcut is None:
                    return
                
                left_shortcut = None
                if dest_widget.left_widget is not None:
                    left_shortcut = dest_widget.left_widget.get_shortcut()
                right_shortcut = None
                if dest_widget.right_widget is not None:
                    right_shortcut = dest_widget.right_widget.get_shortcut()
                    
                self.emit(
                    "application-shortcut-move",
                    source_shortcut, 
                    left_shortcut, 
                    right_shortcut
                    )
        
    def _drag_leave_handler_callback(self, source, destination):
        self.reset()
        
    def _drag_enter_handler_callback(self, source, destination):
        self.expand()
        
    def _drag_end_broadcast_callback(self, source):
        self.reset()
        
    def set_left_separator(self, separator=None):
        self.left = separator
        
    def set_left_widget(self, widget=None):
        self.left_widget = widget
        
    def set_right_separator(self, separator=None):
        self.right = separator
        
    def set_right_widget(self, widget=None):
        self.right_widget = widget
        
    def expand(self):
        _w = 0
        if self.left:
            self.left.set_size_request(self.left.w-10, self.left.h)
            _w += 10
        # At the end of the last row, the final separator
        # before the add/remove icon has a right widget
        # but no right separator
        if self.right_widget:
            if self.right:
                self.right.set_size_request(self.right.w-10, self.right.h)
            _w += 10
        self.set_size_request(self.w+_w, self.h)
        
    def reset(self):
        if self.left:
            self.left.set_size_request(self.left.w, self.left.h)
        if self.right:
            self.right.set_size_request(self.right.w, self.right.h)
        self.set_size_request(self.w, self.h)
