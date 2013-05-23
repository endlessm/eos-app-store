from gi.repository import Gtk
import gettext

from eos_widgets.image_eventbox import ImageEventBox
from eos_util.image import Image
from eos_widgets.desktop_transparent_window import DesktopTransparentWindow

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class DeleteNotPossiblePopupWindow():
    def __init__(self, parent, callback=None, widget=None):
        self._width = 256
        self._height = 225
        
        # Since the TransparentWindow class does not have an option to force centered,
        # for now let's manually calculate the centered position
        # self._window.set_position(Gtk.WIN_POS_CENTER_ALWAYS)
        desktop_size = parent.get_size()
        x = (desktop_size[0] - self._width) / 2
        y = (desktop_size[1] - self._height) / 2
        self._window = DesktopTransparentWindow(parent, (x, y), (self._width, self._height))
        
        self._window.connect("focus-out-event", lambda w, e: self.destroy())
        
        self._fancy_container = ImageEventBox([Image.from_name("feedback-background.png")])
        self._fancy_container.set_size_request(self._width,self._height)
        
        self._close = ImageEventBox([Image.from_name("close.png")])
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_homogeneous(False)
        self._title_label = Gtk.Label()
        self._title_label.set_markup('<span color="#FFFFFF">WARNING!</span>')
        self._title_label.set_alignment(0.6, 0.5)
        self._title_label.set_size_request(220, 24)
        self._close_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._close_box.set_homogeneous(False)
        self._close_box.pack_end(self._close, False, False, 10)
        self._close_box.pack_start(self._title_label, False, False, 0)
        
        self._close_box.set_size_request(24, 24)
        self._container.pack_start(self._close_box, True, False, 0)
        self._bottom_center = Gtk.Alignment()
        self._bottom_center.set(0.5, 1.0, 0, 0)
        self._label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._label_box.set_homogeneous(False)
        
        self._label_box.set_size_request(220, 160)
        self._label = Gtk.Label()
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
