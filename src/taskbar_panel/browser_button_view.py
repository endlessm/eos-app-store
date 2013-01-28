import gtk

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from ui.abstract_notifier import AbstractNotifier
from browser_button_constants import BrowserButtonConstants

class BrowserButtonView(gtk.EventBox, AbstractNotifier):

   def __init__(self):
      gtk.EventBox.__init__(self)

      self.set_visible_window(False)

      normal = load_pixbuf(image_util.image_path("endless-browser.png"))

      image = gtk.Image()
      image.set_from_pixbuf(normal)
      self.add(image)

      self.connect("button-release-event", lambda w, e: self._notify(BrowserButtonConstants.CLICK_EVENT))
