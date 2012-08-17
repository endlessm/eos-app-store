import gtk
from gtk import gdk

from util.image_util import load_pixbuf
import cairo

class IconPlugin(gtk.EventBox):
    SHADOW_OFFSET = 1
    
    def __init__(self, icon_size, icon_name, command):
        super(IconPlugin, self).__init__()
        
        self._command = command
        
        self.set_size_request(icon_size, icon_size)
        
        plugin_image = gtk.Image()
        pixbuf = load_pixbuf(icon_name)
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        
        shadow_pixbuf = scaled_pixbuf

        overlay = scaled_pixbuf.copy()
        shadow_pixbuf.composite(
                                 overlay,
                                 self.SHADOW_OFFSET, self.SHADOW_OFFSET,
                                 overlay.get_width()-self.SHADOW_OFFSET, overlay.get_height()-self.SHADOW_OFFSET,
                                 self.SHADOW_OFFSET, self.SHADOW_OFFSET,
                                 1, 1,
                                 gdk.INTERP_BILINEAR,
                                 255)
            


        
        plugin_image.set_from_pixbuf(overlay)
        
        del pixbuf
        del scaled_pixbuf
        
        self.set_visible_window(False)
        self.add(plugin_image)
        
    def get_launch_command(self):
        return self._command
    
    