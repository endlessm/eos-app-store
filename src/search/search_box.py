import gtk
import gobject
import gettext

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from osapps.app_launcher import AppLauncher
from search.search_box_presenter import SearchBoxPresenter

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class SearchBox(gtk.EventBox):
    HEIGHT = 30
    WIDTH = 234
    LEFT_PADDING = 10
    RIGHT_MARGIN = 33
    BOTTOM_MARGIN = 13

    TOP_MARGIN = 5
    LEFT_MARGIN = 40
    RIGHT_PADDING = 16
    RIGHT_MARGIN_LABEL = 30

    DEFAULT_TEXT = _("Search or Type Web Site")

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.set_visible_window(False)

        self._presenter = SearchBoxPresenter(AppLauncher())

        self.connect('button-press-event', self.gain_focus)
        self._content = gtk.Fixed()

        self._label = SearchBoxLabel(self.DEFAULT_TEXT, self.WIDTH, self.LEFT_MARGIN, self.RIGHT_PADDING, self.RIGHT_MARGIN_LABEL)
        self._button = SearchBoxButton()
        self._frame = SearchBoxFrame()

        self._button.connect('button-press-event', lambda w, e : self._launch_browser(w))

        self._container = SearchBoxContainer(self._button, self._label, self._frame, self.LEFT_MARGIN, self.TOP_MARGIN)

        self._container.set_size_request(self.WIDTH, self.HEIGHT)
        self._content.put(self._container, self.LEFT_PADDING, 0)

        self.add(self._content)
        self._content.show_all()

    def add_text_entry(self, text):
        if hasattr(self, "_text_view"):
            return

        self._text_view = gtk.TextView()
        self._text_buffer = self._text_view.get_buffer()
        self._text_view.set_wrap_mode(gtk.WRAP_NONE)
        self._text_view.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('#303030'))
        self._text_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#f2f1f1'))

        self._text_view.set_size_request(self.WIDTH-self.RIGHT_MARGIN - self.LEFT_MARGIN, self.HEIGHT-self.BOTTOM_MARGIN)

        self._text_view.hide()

        self._text_view.connect("focus-out-event", lambda w, e: self._update_label(w))
        self._text_view.connect("key-press-event", self.handle_keystrokes)

        self._content.put(self._text_view, self._label._LEFT_MARGIN + self.LEFT_PADDING, self.TOP_MARGIN)

    def gain_focus(self, widget, event):

        self.add_text_entry("")

        self._set_label_text("")
        self._text_view.show()
        self._text_view.grab_focus()
        return True

    def _set_label_text(self, text):
        self._label.set_text(text)

    def _update_label(self, widget):
        search_text = self._text_buffer.get_text(self._text_buffer.get_start_iter(), self._text_buffer.get_end_iter(), False)
        self._text_view.hide()
        if len(search_text) > 0:
            self._set_label_text(search_text)
        else:
            self._set_label_text(self.DEFAULT_TEXT)

    def _launch_browser(self, widget):
        self.add_text_entry("")

        search_text = self._text_buffer.get_text(self._text_buffer.get_start_iter(), self._text_buffer.get_end_iter(), False)
        self._text_buffer.set_text("")
        self._text_view.hide()
        self._set_label_text(self.DEFAULT_TEXT)
        self._presenter.launch_search(search_text)

    def handle_keystrokes(self, widget, event):
        if(event.keyval == gtk.keysyms.Escape):
            self._text_buffer.set_text("")
            self._text_view.hide()
            self._set_label_text(self.DEFAULT_TEXT)
            return True
        elif(event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter):
            self._launch_browser(widget)
            return True
        return False

class SearchBoxFrame(gtk.Image):

    def __init__(self):
        gtk.Image.__init__(self)

        self._search_bg_pixbuf = load_pixbuf(image_util.image_path("text_frame_normal.png"))

        self.set_from_pixbuf(self._search_bg_pixbuf)

class SearchBoxLabel(gtk.Label):

    def __init__(self, default_text, width, left_margin, right_padding, right_margin):
        gtk.Label.__init__(self)

        self._LEFT_MARGIN = left_margin
        self._RIGHT_MARGIN = right_margin
        self._RIGHT_PADDING = right_padding
        self._WIDTH=width

        self.set_text(default_text)
        self.set_justify(gtk.JUSTIFY_LEFT)
        self.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#303030'))

    def set_text(self, text):
        max_width = self._WIDTH - (self._LEFT_MARGIN + self._RIGHT_MARGIN)

        shown_text = ""
        for index, letter in enumerate(text):
            shown_text += letter
            layout = self.create_pango_layout(shown_text)
            text_size = layout.get_pixel_size()[0]
            if text_size + self._RIGHT_PADDING >= max_width:
                if index < len(text) - 1:
                    shown_text += "..."
                break

        super(SearchBoxLabel, self).set_text(shown_text)
#        self.set_text(shown_text)

class SearchBoxButton(gtk.EventBox):

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.set_visible_window(False)

        self._internet_pixbuf = load_pixbuf(image_util.image_path("button_browser_normal.png"))
        self._internet_pixbuf_hover = load_pixbuf(image_util.image_path("button_browser_over.png"))
        self._internet_pixbuf_down = load_pixbuf(image_util.image_path("button_browser_down.png"))

        self._internet_image = gtk.Image()
        self.add(self._internet_image)
        self._internet_image.set_from_pixbuf(self._internet_pixbuf)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._internet_image, self._internet_pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._internet_image, self._internet_pixbuf))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._internet_image, self._internet_pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._internet_image, self._internet_pixbuf))

    def toggle_image(self, image, pixbuf):
        image.set_from_pixbuf(pixbuf)

class SearchBoxContainer(gtk.Fixed):


    def __init__(self, button, label, frame, left_margin, top_margin):
        gtk.Fixed.__init__(self)

        self.put(frame, 0, 1)
        self.put(button, 5, 3)

        alignment = gtk.Alignment(0.0, 0.5, 0.0, 0.0)
        alignment.add(label)

        self.put(alignment, left_margin, top_margin)

