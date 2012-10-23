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
        self._window.connect("focus-out-event", lambda w, e: self.destroy())
        
        self._fancy_container = ImageEventBox((image_util.image_path("feedback-background.png"),))
        self._fancy_container.set_size_request(self._width,self._height)
        
        self._close = ImageEventBox((image_util.image_path("close.png"),))
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        
        self._container = gtk.VBox(False)
        self._title_label = gtk.Label()
        self._title_label.set_markup('<span color="#FFFFFF">WARNING!</span>')
        self._title_label.set_alignment(0.6, 0.5)
        self._title_label.set_size_request(220, 24)
        self._close_box = gtk.HBox(False)
        self._close_box.pack_end(self._close, False, False, 10)
        self._close_box.pack_start(self._title_label, False, False, 0)
        
        self._close_box.set_size_request(24, 24)
        self._container.pack_start(self._close_box, True, False, 0)
        self._bottom_center = gtk.Alignment(0.5, 1.0, 0, 0)
        self._label_box = gtk.HBox(False)
        
        self._label_box.set_size_request(220, 160)
        self._label = gtk.Label()
        self._label.set_line_wrap(True)
        
        text = _('To delete a folder you have to\nremove all of the items inside\nof it first.\n\nWe are just trying to\nkeep you safe.')
        self._label.set_markup('<span color="#FFFFFF">' + text + '</span>')
        self._label.set_alignment(0.5, 0.5)
        self._label_box.pack_start(self._label, True, True, 0)
        self._bottom_center.add(self._label_box)
        self._container.pack_start(self._bottom_center, True, False, 0)
        
        
        
        self._fancy_container.add(self._container)
        self._window.add(self._fancy_container)
        self._window.show_all()
    
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
