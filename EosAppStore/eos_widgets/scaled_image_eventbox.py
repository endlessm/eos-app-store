from gi.repository import Gtk
from eos_widgets.image_eventbox import ImageEventBox

class ImageEventBox(ImageEventBox):
    def __init__(self, images):
        ImageEventBox.__init__(self, images)

    def _draw_image(self, image, _draw_method, x, y, w, h):
        image.scale_from_width(w)
        image.draw_centered(_draw_method, x, y, w, h)
