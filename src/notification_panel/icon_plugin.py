import gtk
from gtk import gdk

from util.image_util import load_pixbuf

class IconPlugin(gtk.EventBox):
    def __init__(self, icon_size, icon_name, command):
        super(IconPlugin, self).__init__()
        
        self._command = command
        
        network_configuration_icon = gtk.Image()
        pixbuf = load_pixbuf(icon_name)
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        network_configuration_icon.set_from_pixbuf(scaled_pixbuf)
        
        del pixbuf
        del scaled_pixbuf
        
        self.set_visible_window(False)
        self.add(network_configuration_icon)
        
    def get_launch_command(self):
        return self._command

