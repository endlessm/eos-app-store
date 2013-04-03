import gtk

class ImageEventBox(gtk.EventBox):
    def __init__(self, images):
        gtk.EventBox.__init__(self)
        self.connect("expose-event", self.do_expose_event)
        self._images = images
        self.set_visible_window(False)

    def do_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        self.draw(cr)
        return False

    def draw(self, cr):
        # Get the size and location of the region where the image is to be drawn
        area = self.get_allocation()
        x = area.x
        y = area.y
        w, h = self.size_request()

        # For each image to be composited
        for image in self._images:

            self._transform(image, w, h)

            def _draw_method(pixbuf, x=0, y=0):
                cr.set_source_pixbuf(pixbuf, x, y)

            self._draw_image(image, _draw_method, x, y, w, h)

            cr.paint()

    def _draw_image(self, image, _draw_method, x, y, w, h):
        image.draw_centered(_draw_method, x, y, w, h)

    def _transform(self, image, w, h):
        pass

    def set_images(self, images):
        self._images = images
        self.queue_draw()
