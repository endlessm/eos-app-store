import cairo
import gtk
from util import image_util

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
        area = self.get_allocation()
        x = area.x
        y = area.y
        w, h = self.size_request()
        
        for image in self._images:
            image = image_util.scrub_image_path(image)
            img_surface = cairo.ImageSurface.create_from_png(image)
            cr.set_source_surface(img_surface, x+(w/2-(img_surface.get_width()/2)), y+(h/2-(img_surface.get_height()/2)))
            cr.paint()
    
    def set_images(self, images):
        self._images = images