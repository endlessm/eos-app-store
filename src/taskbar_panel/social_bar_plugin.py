import gtk

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
        
        icon_image = Image.from_name('button_social_normal.png')
        
        icon_image.scale(self._icon_size, self._icon_size)
        icon_image.draw(social_bar_icon.set_from_pixbuf)
        
        return social_bar_icon
    
    
