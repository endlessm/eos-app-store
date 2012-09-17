import gtk
from gtk import gdk

from util.image_util import load_pixbuf

class FeedbackPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(FeedbackPlugin, self).__init__()
        feedback_icon = gtk.Image()
        pixbuf = load_pixbuf('feedback-button.png')
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        feedback_icon.set_from_pixbuf(scaled_pixbuf)
        
        del pixbuf
        del scaled_pixbuf
        
        self.set_visible_window(False)
        self.add(feedback_icon)
