import gtk

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from ui.abstract_notifier import AbstractNotifier
from browser_button_constants import BrowserButtonConstants

class BrowserButtonView(gtk.EventBox, AbstractNotifier):

   def __init__(self):
      gtk.EventBox.__init__(self)
      
      self.set_visible_window(False)

      normal = load_pixbuf(image_util.image_path("button_browser_normal.png"))
      hover = load_pixbuf(image_util.image_path("button_browser_over.png"))

      image = gtk.Image()
      image.set_from_pixbuf(normal)
      self.add(image)

      self.connect("enter-notify-event", lambda w, e: image.set_from_pixbuf(hover))
      self.connect("leave-notify-event", lambda w, e: image.set_from_pixbuf(normal))
      self.connect("button-release-event", lambda w, e: self._notify(BrowserButtonConstants.CLICK_EVENT))
