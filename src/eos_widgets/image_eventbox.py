from gi.repository import Gtk
from gi.repository import Gdk

class ImageEventBox(Gtk.EventBox):
    def __init__(self, images):
        Gtk.EventBox.__init__(self)
	area = Gtk.DrawingArea();
	self.add(area);
        area.connect("draw", self._do_draw)
        self._images = images
        self.set_visible_window(False)

    def _do_draw(self, widget, cr):
        # Get the size and location of the region where the image is to be drawn
        area = self.get_allocation()
        x = area.x
        y = area.y
        size = self.size_request()

        # For each image to be composited
        for image in self._images:

            self._transform(image, size.width, size.height)

            def _draw_method(pixbuf, x=0, y=0):
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
                #cr.set_source_pixbuf(pixbuf, x, y)

            self._draw_image(image, _draw_method, x, y, size.width, size.height)

            cr.paint()
        return False

    def _draw_image(self, image, _draw_method, x, y, w, h):
        image.draw_centered(_draw_method, x, y, w, h)

    def _transform(self, image, w, h):
        pass

    def set_images(self, images):
        self._images = images
        self.queue_draw()
