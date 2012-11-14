import cairo
import gtk
from eos_util import screen_util, image_util
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore

class TransparentWindow(gtk.Window):
    def __init__(self, parent, desktop_preference_class = DesktopPreferencesDatastore, gradient_type=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self._desktop_preferences = desktop_preference_class.get_instance()
        self.gradient_type = gradient_type
        self.set_wmclass("endless_os_desktop", "modal")

        self.set_property("accept-focus", True)
        self.set_property("destroy-with-parent", True)
        self.set_property("focus-on-map", True)

        self.set_transient_for(parent)

        self.set_can_focus(True)
        self.set_can_default(True)

        self.connect("expose-event", self._handle_event)
        self._background = self._desktop_preferences.get_background_pixbuf()
        self.working_area = self._background.get_height()
        
        self._background = self._background.scale_simple(screen_util.get_width(), screen_util.get_height(),gtk.gdk.INTERP_BILINEAR)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_icon(image_util.load_pixbuf('endless.png'))

    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()
        
        self.w = self.allocation.width
        self.h = self.allocation.height
        self.x, self.y = self.window.get_origin()
        self.y -= screen_util.ScreenUtil.get_offset()
        
        cr.set_source_rgba(0, 0, 0, 255)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        self.draw(cr)

        self.show_all()

        return False

    def draw(self, cr):
        pixbuf = self._background.subpixbuf(self.x, self.y, self.w, self.h)
        cr.set_source_pixbuf(pixbuf, 0, 0)
        if self.gradient_type is None:
            w, h = self.size_request()
            pixbuf = self._background.subpixbuf(x, y, w, h)
            cr.set_source_pixbuf(pixbuf, 0, 0)

            cr.paint()
        else:
            gradient = cairo.LinearGradient(0, 0, 0, self.h)
            gradient.add_color_stop_rgba(0.005, 255, 255, 255, 0)
            gradient.add_color_stop_rgba(0.006, 0, 0, 0, 0.7)
            gradient.add_color_stop_rgba(0.994, 0, 0, 0, 0.0)
            gradient.add_color_stop_rgba(0.995, 255, 255, 255, 0)
            cr.mask(gradient)
            cr.fill()
        
        #self.queue_draw()
        
        return False
