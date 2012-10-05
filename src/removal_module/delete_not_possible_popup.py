import gtk
import gettext
from util.image_eventbox import ImageEventBox
from util import image_util
from util.transparent_window import TransparentWindow
import gobject

class DeleteNotPossiblePopupWindow():
    def __init__(self, callback=None, parent=None, widget=None):
        self._width = 256
        self._height = 225
        
        self._window = TransparentWindow(parent)
        self._window.set_size_request(self._width,self._height)
        self._window.set_title(_("WARNING!"))
        self._window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        
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
        
        self._label_box = gtk.HBox(True)
        self._label = gtk.Label()
        self._label.set_text('To delete a folder you have to remove all of the items inside of it first. We are just trying to keep you safe.')
        self._label_box.pack_start(self._label, False, False, 0)
        self._container.pack_start(self._label_box, True, False, 0)
        
        
        
        self._fancy_container.add(self._container)
        self._window.add(self._fancy_container)
        self._window.show_all()
    
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
