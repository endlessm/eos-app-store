from gi.repository import Gtk
from gi.repository import GdkPixbuf
import cairo
from eos_util import image_util
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from application_row_box import ApplicationRowBox

class AddApplicationBox(Gtk.Box):
    def __init__(self, parent, presenter, width, height, add_remove_widget=None, desktop_preference_class = DesktopPreferencesDatastore, default_category='All'):
        super(AddApplicationBox, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_homogeneous(True)

        #self._presenter = parent._presenter
        self._presenter = presenter
        self._parent = parent
        self.x = 0
        self.y = 0
        self._refresh = True
        self._scrolling = False

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.connect("show", self._on_show)
        self._scrolled_window.get_vscrollbar().connect("value-changed", self._on_scroll)

        self._active_category = default_category
        apps = self._presenter.get_category(self._active_category)
        self._fill_applications(apps)

        self._vbox.set_homogeneous(False)
        self._vbox.connect("draw", self._handle_draw)
        self._scrolled_window.add_with_viewport(self._vbox)
        self.add(self._scrolled_window)
        self.show_all()

    def _fill_applications(self, apps):
        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if apps:
            for app in apps:
                self._display_application(app)

    def _display_application(self, app):
        row = ApplicationRowBox(app, parent=self, presenter=self._presenter)
        row.connect("enter-notify-event", self._draw_active, row)
        row.connect("leave-notify-event", self._draw_inactive, row)
        self._vbox.pack_start(row, True, True, 0)

    def _on_show(self, widget):
        widget.get_child().set_shadow_type(Gtk.ShadowType.NONE)

    def _on_scroll(self, widget):
        self._scrolled_window.queue_draw()

    def _handle_draw(self, widget, cr):
        x, y, _ = self._vbox.get_window().get_origin()
        top_x, top_y, _ = self._scrolled_window.get_window().get_toplevel().get_origin()
        self.draw(cr, x - top_x, y - top_y, self.get_allocation().width, self.get_allocation().height)

        # TODO what is the purpose of self._refresh?
        # In the current implementation, things look better for the website box
        # without the check, so I'm disabling it here as well
        # if not self._refresh and event:
        #if event:
#           self._draw_gradient(cr, event.area.width, event.area.height, event.area.x, event.area.y)

        return False

    def draw(self, cr, x, y, w, h):
        self._scrolled_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
        # Only copy/crop the background the first time through
        # to avoid needless memory copies and image manipulation
        if not self._scrolling:
            self._scrolling = True
        scroll_y = self._scrolled_window.get_vscrollbar().get_value()
        cr.paint()

    def _draw_gradient(self, cr, w, h, x=0, y=0):
        pat = cairo.LinearGradient (0.0, 0.0, w, 0.0)
        pat.add_color_stop_rgba (0.001, 0.0, 0.0, 0.0, 0.8)
        pat.add_color_stop_rgba (1, 0.2, 0.2, 0.2, 0.8)

        cr.rectangle(x, y, w, h)
        cr.set_source(pat)
        cr.fill()

    def _draw_active(self, widget, event, row):
        self._refresh = False
        widget.name_label.set_markup('<span color="#ffffff" font="Novecento wide" font_weight="bold">' + widget._name + '</span>')
        widget.description_label.set_markup('<span color="#ffffff" font-style="italic">' + widget._description + '</span>')
        widget._plus_image.set_from_file(image_util.image_path("add_folder_icon.png"))
        widget._plus_image.show()
        pixbuf = image_util.load_pixbuf(image_util.image_path('category_separator_inactive.png'))
        pixbuf = pixbuf.scale_simple(self.get_allocation().width, pixbuf.get_height(), GdkPixbuf.InterpType.BILINEAR)
        widget._bottom_active_line.set_from_pixbuf(pixbuf)
        widget._top_active_line.set_from_pixbuf(pixbuf)
        widget.queue_draw()

        return False

    def _draw_inactive(self, widget, event, row=None):
        self._refresh = True
        widget.name_label.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold">' + widget._name + '</span>')
        widget.description_label.set_markup('<span color="#aaaaaa" font-style="italic">' + widget._description + '</span>')
        widget._plus_image.hide()
        widget._bottom_active_line.set_from_pixbuf(None)
        widget._top_active_line.set_from_pixbuf(None)
        widget.queue_draw()

        return False

    def install_app(self, application_model):
        self._parent.install_app(application_model)
        self._parent.destroy(None, None)

