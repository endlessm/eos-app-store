import gtk

from eos_util.image import Image

class FeedbackPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(FeedbackPlugin, self).__init__()
        feedback_icon = gtk.Image()
        
        icon_image = Image.from_name('feedback-button.png')
        
        icon_image.scale(icon_size, icon_size)
        icon_image.draw(feedback_icon.set_from_pixbuf)
        
        self.set_visible_window(False)
        self.add(feedback_icon)
