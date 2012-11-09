import cairo
import gtk
from gtk import gdk
from util import image_util
import rsvg

class ImageEventBox(gtk.EventBox):
    def __init__(self, images, width = 0):
        gtk.EventBox.__init__(self)
        self.connect("expose-event", self.do_expose_event)
        self._images = images
        self._width = width
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
            
            if self._width > 0 or image.endswith('.xpm'):
                self._draw_pixbuf(cr, image_util.load_pixbuf(image), x, y, w, h)
            else:
                if '.svg' in image:
                    try:
                        svg = rsvg.Handle(file=image)
                    except:
                        print 'Error. Could not open', image
                        break
                    img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 48, 48)
                    cx = cairo.Context(img_surface)
                    svg.render_cairo(cx)
                    del cx
                    cr.set_source_surface(img_surface, x+(64/2-(img_surface.get_width()/2)), y+(64/2-(img_surface.get_height()/2)))
                else:
                    img_surface = cairo.ImageSurface.create_from_png(image)
                    offset_x = x+(w/2-(img_surface.get_width()/2))
                    offset_y = y+(h/2-(img_surface.get_height()/2))
                
                    cr.set_source_surface(img_surface, offset_x, offset_y)
                cr.paint()
    
    def _draw_pixbuf(self, cr, pixbuf, x, y, w, h):
        # If we want a specific width, scale it
        # otherwise scale to whatever the requested size is
        if self._width:
            scaled_pixbuf = pixbuf.scale_simple(self._width, pixbuf.get_height(), gdk.INTERP_BILINEAR)
            cr.set_source_pixbuf(scaled_pixbuf, 0, 0)
        else:
            aspect_ratio = w / float(pixbuf.get_width())
            scaled_pixbuf = pixbuf.scale_simple(w, int(pixbuf.get_height() * aspect_ratio), gdk.INTERP_BILINEAR)
            cr.set_source_pixbuf(scaled_pixbuf, x+(w/2-(scaled_pixbuf.get_width()/2)), y+(h/2-(scaled_pixbuf.get_height()/2)))
            
        del scaled_pixbuf
        del pixbuf

    def set_images(self, images):
        self._images = images
        self.repaint()
        
    def repaint(self):
        #self.do_expose_event(self, None)
        if hasattr(self, 'parent') and hasattr(self.parent, 'parent'):
            self.parent.parent.queue_draw()
        
