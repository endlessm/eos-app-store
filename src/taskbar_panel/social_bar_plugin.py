import gtk
from gtk import gdk

from eos_util.image_util import load_pixbuf
from eos_util.image import Image
import math

class SocialBarPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(SocialBarPlugin, self).__init__()
        self._icon_size = icon_size
        
        self.add(self._create_icon())
        self.show_all()
        self.set_visible_window(False)
    
    def _create_icon(self):
        icon_wrapper = gtk.EventBox()
        icon_wrapper.set_visible_window(False)
        
#        icon_wrapper.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=65535))
        
        icon_wrapper.connect("expose-event", self._draw_notification_area)
        icon_wrapper.add(self._create_static_icon())
        
        return icon_wrapper
    
    def _create_static_icon(self):
        print "There"
        social_bar_icon = gtk.Image()
        pixbuf = load_pixbuf('feedback-button.png')
        icon_image = Image(pixbuf)
        icon_image.scale(self._icon_size, self._icon_size)
        social_bar_icon.set_from_pixbuf(icon_image.pixbuf)        
        
        del pixbuf
        del icon_image
        
        return social_bar_icon
    
    
    def _draw_notification_area(self, widget, event):
        cr = widget.window.cairo_create()
        cr.save()
        # clip to dimensions of widget
        cr.rectangle(event.area.x, event.area.y,
                    event.area.width + 10, event.area.height + 10)
        cr.clip()
        
        cr.set_line_width(1)
        width = event.area.width + 6.0
        height = event.area.height + 6.0
        pi = math.pi
#        
        cr.set_source_rgb(1.0, 0.0, 0.0)
        radius = min(width / 2.0, height / 2.0)
        cr.arc(event.area.x+width / 2.0, event.area.y + height / 2.0, radius, 0, 2.0 * pi)
        
        cr.fill()
        print "HERE"
        
        return False
    
