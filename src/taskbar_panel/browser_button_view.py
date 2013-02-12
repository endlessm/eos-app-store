import gtk

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from eos_widgets.abstract_notifier import AbstractNotifier
from browser_button_constants import BrowserButtonConstants

class BrowserButtonView(gtk.EventBox, AbstractNotifier):
    
    ICON_SIZE = BrowserButtonConstants.ICON_SIZE
    PADDED_WIDTH = ICON_SIZE + BrowserButtonConstants.BROWSER_ICON_PADDING

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.set_visible_window(False)

        normal = load_pixbuf(image_util.image_path("endless-browser.png"))

        image = gtk.Image()
        image.set_from_pixbuf(normal.scale_simple(self.ICON_SIZE, self.ICON_SIZE, gtk.gdk.INTERP_BILINEAR))

        # Add some margin
        self.set_size_request(self.PADDED_WIDTH, self.ICON_SIZE)
        
        self.add(image)

        self.connect("button-release-event", lambda w, e: self._notify(BrowserButtonConstants.CLICK_EVENT))
