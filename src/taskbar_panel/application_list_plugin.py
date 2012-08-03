import gtk
from gtk import gdk

from util.image_util import load_pixbuf

class ApplicationListPlugin(gtk.HBox):
    def __init__(self, icon_size):
        super(ApplicationListPlugin, self).__init__()
        pixbuf = load_pixbuf('bluetooth.png')
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        
        del pixbuf
        
        for count in range(4):
            self._application_event_box = gtk.EventBox()
            self._application_event_box.set_visible_window(False)
    
            self._icon = gtk.Image()
            self._icon.set_from_pixbuf(scaled_pixbuf)
            self._application_event_box.add(self._icon)
            
            self.pack_start(self._application_event_box, False, False, 4)
            
        del scaled_pixbuf
        
        self.show_all()
        
        
