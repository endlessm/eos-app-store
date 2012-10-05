import gtk
import gettext
from util.image_eventbox import ImageEventBox
from util import image_util
from util.transparent_window import TransparentWindow
import gobject

class RemovalConfirmationPopupWindow():
    def __init__(self, callback, parent=None, widget=None, label=None):
        self._width = 256
        self._height = 225
        
        self._window = TransparentWindow(parent)
        self._window.set_size_request(self._width,self._height)
        self._window.set_title(_("DELETE?"))
        self._window.set_position(gtk.WIN_POS_MOUSE)
        #self._window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        
        self._fancy_container = ImageEventBox((image_util.image_path("feedback-background.png"),))
        self._fancy_container.set_size_request(self._width,self._height)
        self._center = gtk.Alignment(.5,.3,0,0)
        
        self._close = ImageEventBox((image_util.image_path("close.png"),))
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        
        self._container = gtk.VBox(False)
        
        self._close_box = gtk.HBox(False)
        self._close_box.pack_end(self._close, False, False, 0)
        
        self._container.pack_start(self._close_box, True, False, 0)
        
        self._button_box = gtk.HBox(True)
        self._button_box.set_size_request(75,30)
        
        # this should be replaced with round button image with x on it
        self._cancel_button = gtk.Button(label='Cancel')
        self._cancel_button.connect("button-release-event", lambda w, e: callback(False, widget, label))
        self._cancel_button.connect("button-release-event", lambda w, e: self.destroy())
        
        # this should be replaced with round button image with checkmark on it
        self._ok_button = gtk.Button(label='OK')
        self._ok_button.connect("button-release-event", lambda w, e: callback(True, widget, label))
        self._ok_button.connect("button-release-event", lambda w, e: self.destroy())
        
        self._button_box.pack_start(self._cancel_button, True, True)
        self._button_box.pack_start(self._ok_button, True, True)
        
        self._container.pack_start(self._button_box, True, True, 5)
        
        self._fancy_container.add(self._container)
        self._window.add(self._fancy_container)
        self._window.show_all()
    
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
