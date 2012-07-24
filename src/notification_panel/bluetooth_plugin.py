import gtk
from gtk import gdk

from util.image_util import load_pixbuf

class BluetoothSettingsPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(BluetoothSettingsPlugin, self).__init__()
        network_configuration_icon = gtk.Image()
        pixbuf = load_pixbuf('bluetooth.png')
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        network_configuration_icon.set_from_pixbuf(scaled_pixbuf)
        
        del pixbuf
        del scaled_pixbuf
        
        self.set_visible_window(False)
        self.add(network_configuration_icon)
        
    @staticmethod
    def get_launch_command():
        return 'gnome-control-center --class=eos-network-manager bluetooth'