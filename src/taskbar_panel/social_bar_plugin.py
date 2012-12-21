import gtk

from eos_util.image_util import load_pixbuf
from eos_util.image import Image

class SocialBarPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(SocialBarPlugin, self).__init__()
        self._icon_size = icon_size
        
        self.add(self._create_static_icon())
        self.show_all()
        self.set_visible_window(False)
    
    def _create_static_icon(self):
        social_bar_icon = gtk.Image()
        pixbuf = load_pixbuf('button_social_normal.png')
        icon_image = Image(pixbuf)
        icon_image.scale(self._icon_size, self._icon_size)
        social_bar_icon.set_from_pixbuf(icon_image.pixbuf)        
        
        del pixbuf
        del icon_image
        
        return social_bar_icon
    
    
