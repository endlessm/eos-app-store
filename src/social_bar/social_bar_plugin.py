import gtk

from eos_util.image import Image
from social_bar.social_bar_presenter import SocialBarPresenter

class SocialBarPlugin(gtk.EventBox):
    
    def __init__(self, parent, icon_size):
        super(SocialBarPlugin, self).__init__()
        self._icon_size = icon_size
        self._presenter = SocialBarPresenter()

        self._parent = parent

        self._pixbuf_normal = Image.from_name('user-icon_normal.png').scale(icon_size, icon_size)
        self._pixbuf_hover = Image.from_name('user-icon_hover.png').scale(icon_size, icon_size)
        self._pixbuf_down = Image.from_name('user-icon_down.png').scale(icon_size, icon_size)

        self._social_icon = gtk.Image()

        self._pixbuf_normal.draw(self._social_icon.set_from_pixbuf)

        self.add(self._social_icon)
        self.show_all()
        self.set_visible_window(False)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._social_icon, self._pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._social_icon, self._pixbuf_normal))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._social_icon, self._pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._social_icon, self._pixbuf_normal))

        self.connect('button-press-event', lambda w, e: self._social_bar_icon_clicked_callback())

    def get_path(self):
        return self._presenter.get_path()

    def toggle_image(self, image, pixbuf):
        pixbuf.draw(image.set_from_pixbuf)


    def _social_bar_icon_clicked_callback(self):
        self._presenter.launch()
