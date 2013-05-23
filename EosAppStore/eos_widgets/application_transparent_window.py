import transparent_window
from EosAppStore.eos_util.image import Image
from gi.repository import Gtk

# This type of transparent window extracts the background from the parent window
# This is useful when the transparency should show the image from an application
# rather than the underlying desktop background

class ApplicationTransparentWindow(transparent_window.TransparentWindow):
    
    def __init__(self, parent, location=(0,0), size=None, gradient_type=None):
        size = size or parent.get_size()
        width, height = size
        x, y = location
        
        background = None 
        
        super(ApplicationTransparentWindow, self).__init__(parent, background, location, size, gradient_type)
