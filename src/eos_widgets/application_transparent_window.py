import transparent_window
from eos_util.image import Image
import gtk

# This type of transparent window extracts the background from the parent window
# This is useful when the transparency should show the image from an application
# rather than the underlying desktop background

class ApplicationTransparentWindow(transparent_window.TransparentWindow):
    
    def __init__(self, parent, location=(0,0), size=None, gradient_type=None):
        size = size or parent.get_size()
        width, height = size
        x, y = location
        
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
        background = Image(pixbuf.get_from_drawable(parent.window, parent.get_colormap(), x, y, 0, 0, width, height))
        
        super(ApplicationTransparentWindow, self).__init__(parent, background, location, size, gradient_type)
