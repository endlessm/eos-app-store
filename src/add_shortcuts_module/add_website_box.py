import gtk
import cairo
from eos_util import image_util
from eos_util import screen_util
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from website_row_box import WebsiteRowBox

class AddWebsiteBox(gtk.VBox):
    def __init__(self, parent=None, desktop_preference_class = DesktopPreferencesDatastore, default_category=''):
        super(AddWebsiteBox, self).__init__()
        self.set_homogeneous(False)

        self._presenter = parent._presenter
        self._parent = parent
        self._vbox = gtk.VBox()
        self._vbox.set_homogeneous(False)
        self._scrolling = False
        self._refresh = True

        self._desktop_preferences = desktop_preference_class.get_instance()
        self._background = self._desktop_preferences.get_scaled_background_image(
                screen_util.get_width(parent.window), screen_util.get_height(parent.window))
        
        self._scrolled_window = gtk.ScrolledWindow()
        self._scrolled_window.set_policy(hscrollbar_policy=gtk.POLICY_NEVER, vscrollbar_policy=gtk.POLICY_AUTOMATIC)
        self._scrolled_window.connect("show", self._on_show)
        self._scrolled_window.get_vscrollbar().connect("value-changed", self._on_scroll)

        label_text = _('SEARCH FOR A WEBSITE')
        self._label = gtk.Label()
        self._label.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold" size="16000">' + label_text + '</span>')

        self._text_entry_align = gtk.Alignment(0.5, 0.5, 0, 0)
        self._hbox = gtk.HBox()
        self._hbox.set_size_request(286, 24)
        self._text_entry = gtk.Entry(50)
        self._text_entry.connect("focus-in-event", self._handle_focus_in)
        self._text_entry.connect("focus-out-event", self._handle_focus_out)

        self._text_entry.set_alignment(0.5)
        self._hbox.pack_start(self._text_entry)
        self._text_entry.set_text(_('Type it here'))
        self._text_entry_align.add(self._hbox)


        self.hbox_separator = gtk.HBox()
        self.hbox_separator.set_size_request(-1, 15)
        self._vbox.pack_start(self.hbox_separator, False, False, 0)
        self._vbox.pack_start(self._label, False, False, 0)
        self._vbox.pack_start(self._text_entry_align, False, False, 20)
        self.hbox_separator1 = gtk.HBox()
        self.hbox_separator1.set_size_request(-1, 15)
        self.hbox_separator1.connect("expose-event", self._draw_divider_line)
        self._vbox.pack_start(self.hbox_separator1, False, False, 0)

        sites = self._presenter.get_recommended_sites()
        self._fill_sites(sites)

        self._vbox.connect("expose-event", self._handle_expose_event)
        self._text_entry.connect("activate", self._handle_key_press)
        self._scrolled_window.add_with_viewport(self._vbox)
        self.add(self._scrolled_window)
        self.show_all()

    def _fill_sites(self, sites):
        for site in sites:
            self._display_site(site)

    def _display_site(self, site):
        row = WebsiteRowBox(site, parent=self, presenter=self._presenter)
        row.connect("enter-notify-event", self._draw_active, row)
        row.connect("leave-notify-event", self._draw_inactive, row)
        self._vbox.pack_start(row, False, False, 0)

    def _on_show(self, widget):
        widget.get_child().set_shadow_type(gtk.SHADOW_NONE)
        
    def _on_scroll(self, widget):
        self._scrolled_window.queue_draw()
        
    def _handle_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        x, y = self._vbox.window.get_origin()
        top_x, top_y = self._scrolled_window.window.get_toplevel().get_origin()
        self.draw(cr, x - top_x, y - top_y, self.allocation.width, self.allocation.height)
        
        # TODO what is the purpose of self._refresh?
        # In the current implementation, things look better without the check
        # if not self._refresh and event:
        if event:
            self._draw_gradient(cr, event.area.width, event.area.height, event.area.x, event.area.y)

        return False

    def draw(self, cr, x, y, w, h):
        # Only copy/crop the background the first time through
        # to avoid needless memory copies and image manipulation
        if not self._scrolling:
            self._background = self._background.copy().crop(x, 0, w, h)
            self._scrolling = True
        scroll_y = self._scrolled_window.get_vscrollbar().get_value()
        self._background.draw(lambda pixbuf: cr.set_source_pixbuf(pixbuf, 0, scroll_y))
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
        widget.description_label.set_markup('<span color="#ffffff" font-style="italic">' + widget._item._url + '</span>')
        widget._plus_image.set_from_file(image_util.image_path("add_folder_icon.png"))
        widget._plus_image.show()
        pixbuf = image_util.load_pixbuf(image_util.image_path('category_separator_inactive.png'))
        pixbuf = pixbuf.scale_simple(self.allocation.width, pixbuf.get_height(), gtk.gdk.INTERP_BILINEAR)
        widget._bottom_active_line.set_from_pixbuf(pixbuf)
        widget._top_active_line.set_from_pixbuf(pixbuf)
        widget.draw(widget.get_allocation())

        return False

    def _draw_inactive(self, widget, event, row):
        self._refresh = True
        widget.name_label.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold">' + widget._name + '</span>')
        widget.description_label.set_markup('<span color="#aaaaaa" font-style="italic">' + widget._item._url + '</span>')
        widget._plus_image.hide()
        widget._bottom_active_line.set_from_pixbuf(None)
        widget._top_active_line.set_from_pixbuf(None)
        widget.draw(widget.get_allocation())

        return False

    def _draw_divider_line(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, 1)
        cr.set_source_rgba(0.08, 0.08, 0.08, 0.8)
        cr.fill()
        cr.rectangle(event.area.x, event.area.y+1, event.area.width, 1)
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
        cr.fill()

    def _handle_focus_in(self, widget, event):
        widget.set_text('')

    def _handle_focus_out(self, widget, event):
        widget.set_text('')

    def _handle_key_press(self, widget):
        if widget.get_text():
            site = self._presenter.get_custom_site_shortcut(widget.get_text())
            if site:
                self.install_site(site)
            else:
                widget.set_text('Url invalid, please try again')
                widget.select_region(0, -1)

    def install_site(self, site):
        self._parent.install_site(site)
        self._parent.destroy(None, None)
