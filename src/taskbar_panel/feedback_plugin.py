import gtk
from gtk import gdk

from eos_util.image_util import load_pixbuf

class FeedbackPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(FeedbackPlugin, self).__init__()
        
        self._pixbuf_normal = load_pixbuf('report-icon_normal.png').scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        self._pixbuf_hover = load_pixbuf('report-icon_hover.png').scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        self._pixbuf_down = load_pixbuf('report-icon_down.png').scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        
        self._feedback_icon = gtk.Image()
        self._feedback_icon.set_from_pixbuf(self._pixbuf_normal)
        self.set_visible_window(False)
        self.add(self._feedback_icon)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_normal))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_norma))

    def toggle_image(self, image, pixbuf):
        image.set_from_pixbuf(pixbuf)
