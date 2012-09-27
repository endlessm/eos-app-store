import gobject
import string
import gtk.keysyms
import gtk
from shortcut.desktop_shortcut import DesktopShortcut



class SeparatorShortcut(DesktopShortcut):

    left = None
    right = None
    expanded = False
    _all_separators = set()
    
    def __init__(self, width=30, height=64):
        super(SeparatorShortcut, self).__init__('')
        # listen for motion on all widgets
        DesktopShortcut._add_motion_broadcast_callback(
            SeparatorShortcut._motion_broadcast_callback
            )
        self.w = width
        self.h = height
        self.set_size_request(self.w, self.h)
        self.class_name = 'sch_sep'
        self._sep_obj = self
        SeparatorShortcut._all_separators.add(self)
        self._image_name = ''
        self._show_background = True
        self.show_all()
        
    # DND Callbacks
    def _transmiter_handler_callback(self, source):
        print 
        print '-> SeparatorShortcut::_transmiter_handler_callback'
        print '    source', source
        return 'some random data'
     
    def _received_handler_callback(self, source, destination, x, y, data=None):
        print 
        print '-> SeparatorShortcut::_received_handler_callback'
        print '    source', source
        print '    tdestination', destination
        print '    x:%s, y:%s' % (x, y)
        print '    data', data

    def _motion_handler_callback(self, source, destination, x, y):
        print 
        print '-> SeparatorShortcut::_motion_handler_callback'
        print '    source', source
        print '    destination', destination
        print '    x:%s, y:%s' % (x, y)
    #
    @classmethod
    def _motion_broadcast_callback(cls, source, destination, x, y):
        print 
        print '-> [BC] SeparatorShortcut::_motion_broadcast_callback'
        print '    source', source
        print '    destination', destination
        print '    x:%s, y:%s' % (x, y)
    
            
    @classmethod
    def _reset_all(cls):
        for sep in cls._all_separators:
            sep.reset()
        
    def SetLeft(self, separator=None):
        self.left = separator
        
    def SetRight(self, separator=None):
        self.right = separator
        
    def expand(self):
        print 'expanding: ', self
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
        print 'reseting: ', self
        if self.left:
            self.left.set_size_request(self.left.w, self.left.h)
        if self.right:
            self.right.set_size_request(self.right.w, self.right.h)
        self.set_size_request(self.w, self.h)
        self.expanded = False
        