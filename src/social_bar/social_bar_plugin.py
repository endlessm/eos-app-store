import gtk

from eos_util.image import Image
from social_bar.social_bar_popup_window import SocialBarPopupWindow

class SocialBarPlugin(gtk.EventBox):
    PATH = "/usr/bin/eos-social"
    def __init__(self, parent, icon_size):
        super(SocialBarPlugin, self).__init__()
        self._icon_size = icon_size

        self._parent = parent
        self.add(self._create_static_icon())
        self.show_all()
        self.set_visible_window(False)

        self.connect('button-press-event', lambda w, e:self._social_bar_icon_clicked_callback())

    def _create_static_icon(self):
        social_bar_icon = gtk.Image()

        icon_image = Image.from_name('button_social_normal.png')

        icon_image.scale(self._icon_size, self._icon_size)
        icon_image.draw(social_bar_icon.set_from_pixbuf)

        return social_bar_icon


    def _social_bar_icon_clicked_callback(self):        
        self._social_bar_popup = SocialBarPopupWindow(self._parent)
        self._social_bar_popup.show()
