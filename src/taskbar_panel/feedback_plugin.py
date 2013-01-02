import gtk

from eos_util.image import Image

class FeedbackPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(FeedbackPlugin, self).__init__()
 
        self._pixbuf_normal = Image.from_name('report-icon_normal.png').scale(icon_size, icon_size)
        self._pixbuf_hover = Image.from_name('report-icon_hover.png').scale(icon_size, icon_size)
        self._pixbuf_down = Image.from_name('report-icon_down.png').scale(icon_size, icon_size)
        
        self._feedback_icon = gtk.Image()
        
        self._pixbuf_normal.draw(self._feedback_icon.set_from_pixbuf)
        
        self.set_visible_window(False)
        self.add(self._feedback_icon)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_normal))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_normal))

    def toggle_image(self, image, pixbuf):
        pixbuf.draw(image.set_from_pixbuf)
