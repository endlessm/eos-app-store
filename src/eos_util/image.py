import image_util
from gi.repository import Gdk

class Image:

    def __init__(self, pixbuf, path = None):
        self._pixbuf = pixbuf
        self._path = path

    @staticmethod
    def from_path(path):
        path = image_util.scrub_image_path(path)
        pixbuf = image_util.load_pixbuf(path)
        return Image(pixbuf, path)

    @staticmethod
    def from_name(image_name):
        path = image_util.image_path(image_name)
        return Image.from_path(path)

    @property
    def width(self):
        return self._pixbuf.get_width()

    @property
    def height(self):
        return self._pixbuf.get_height()

    @property
    def pixbuf(self):
        return self._pixbuf

    def __str__(self):
        return 'Image(' + repr(self._path) + ")"

    def stretch_horizontal(self, width):
        self.scale(width, self.height)
        return self

    def scale_from_width(self, width):
        aspect_ratio = width / float(self.width)
        height = int(self.height * aspect_ratio)
        self.scale(width, height)
        return self

    def scale_from_height(self, height):
        aspect_ratio = height / float(self.height)
        width = int(self.width * aspect_ratio)
        self.scale(width, height)
        return self

    def draw(self, method):
        method(self._pixbuf)

    def draw_centered(self, method, x, y, w, h):
        image = self
        width = self.width
        height = self.height
        if (width > w) or (height > h):
            image = self.copy().scale_to_best_fit(w, h)
            width = image.width
            height = image.height
        x = x + (w - width) / 2
        y = y + (h - height) / 2
        method(image._pixbuf, x, y)

    def scale_to_best_fit(self, area_width, area_height):
        vertical_scale_factor = area_height/float(self.height)
        horizontal_scale_factor = area_width/float(self.width)

        horizontal_scale_factor_applied_to_height = horizontal_scale_factor * self.height

        vertical_scale_factor_applied_to_width =  vertical_scale_factor * self.width

        new_width = 0
        new_height = 0
        # given scale factors that scale the image to best fit horizontally or
        # vertically, which of these results in the images fitting best, ie
        # covering the whole screen without black borders.
        if (horizontal_scale_factor_applied_to_height < area_height):
            new_height = area_height
            new_width = vertical_scale_factor_applied_to_width
        else:
            new_height = horizontal_scale_factor_applied_to_height
            new_width = area_width
        self.scale(int(new_width), int(new_height))
        return self

    def scale(self, width, height):
        self._pixbuf = self._pixbuf.scale_simple(width, height, gdk.INTERP_BILINEAR)
        return self

    def crop(self, x, y, width, height):
        self._pixbuf = self._pixbuf.subpixbuf(x, y, width, height)
        return self

    def copy(self):
        return Image(self._pixbuf.copy())
