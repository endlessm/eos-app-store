import gtk
import gobject
import gettext

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from search.search_box_model import SearchBoxModel
from search.search_box_presenter import SearchBoxPresenter
from search.search_box_constants import SearchBoxConstants
from eos_widgets.abstract_notifier import AbstractNotifier

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class SearchBox(gtk.EventBox, AbstractNotifier):
    HEIGHT = 30
    WIDTH = 298
    LEFT_PADDING = 10
    RIGHT_MARGIN = 15
    BOTTOM_MARGIN = 8

    TOP_MARGIN = 6
    LEFT_MARGIN = 40
    RIGHT_PADDING = 16
    RIGHT_MARGIN_LABEL = 30

    DEFAULT_TEXT = _("Google or type website")

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.set_visible_window(False)

        SearchBoxPresenter(self, SearchBoxModel())

        self.connect('button-release-event', self.gain_focus)

        self._content = gtk.Fixed()

        self._label = SearchBoxLabel(self.DEFAULT_TEXT, self.WIDTH, self.LEFT_MARGIN, self.RIGHT_PADDING, self.RIGHT_MARGIN_LABEL)
        self._button = SearchBoxButton()
        self._frame = SearchBoxFrame()

        self._button.connect('button-release-event', lambda w, e : self._notify(SearchBoxConstants.LAUNCH_BROWSER))

        self._container = SearchBoxContainer(self._button, self._label, self._frame, self.LEFT_MARGIN, self.TOP_MARGIN)

        self._container.set_size_request(self.WIDTH, self.HEIGHT)
        self._content.put(self._container, self.LEFT_PADDING, 0)

        self.add(self._content)
        self._content.show_all()

    def add_text_entry(self, text):
        if hasattr(self, "_text_view"):
            text_buffer = gtk.TextBuffer()
            text_buffer.set_text(text)
            self._text_view.set_buffer(text_buffer)

            return

        self._text_view = gtk.TextView()

        self._text_view.set_wrap_mode(gtk.WRAP_NONE)
        self._text_view.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('#fff'))
        # TODO Make the text background transparent -- for now, use a solid color that is similar to the default background
        self._text_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#383020'))

        self._text_view.set_size_request(self.WIDTH-self.RIGHT_MARGIN - self.LEFT_MARGIN, self.HEIGHT-self.BOTTOM_MARGIN)
        self._text_view.set_left_margin(5)
        self._text_view.set_pixels_above_lines(3)

        self._text_view.hide()

        self._text_view.connect("focus-out-event", lambda w, e: self._update_label(w))
        self._text_view.connect("key-press-event", self.handle_keystrokes)

        self._content.put(self._text_view, self._label._LEFT_MARGIN + self.LEFT_PADDING, self.TOP_MARGIN)

    def gain_focus(self, widget, event):
        self._frame.disable_roll_over()

        search_text = self._label.get_label()
        if search_text == self.DEFAULT_TEXT:
            search_text = ""

        self.add_text_entry(search_text)

        self._set_label_text("")
        self._text_view.show()
        self._text_view.grab_focus()
        return True

    def _set_label_text(self, text):
        self._label.set_text(text)

    def _update_label(self, widget):
        text_buffer = self._text_view.get_buffer()
        search_text = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), False)
        self.reset_text_field()
        if len(search_text) > 0:
            self._set_label_text(search_text)
        else:
            self._set_label_text(self.DEFAULT_TEXT)

    def get_search_text(self):
        search_text = ""
        if hasattr(self, "_text_view"):
            text_buffer = self._text_view.get_buffer()
            search_text = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), False)
        return search_text

    def reset_search(self):
        self.add_text_entry("")
        self.reset_text_field()

    def reset_text_field(self):
        text_buffer = self._text_view.get_buffer()
        text_buffer.set_text("")
        self._text_view.hide()
        self._set_label_text(self.DEFAULT_TEXT)
        self._frame.enable_roll_over()

    def handle_keystrokes(self, widget, event):
        if(event.keyval == gtk.keysyms.Escape):
            self.reset_text_field()
            return True
        elif(event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter):
            self._notify(SearchBoxConstants.LAUNCH_BROWSER)
            return True
        return False

class SearchBoxFrame(gtk.EventBox):

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.set_visible_window(False)

        search_normal = load_pixbuf(image_util.image_path("search-box_normal.png"))
        search_hover = load_pixbuf(image_util.image_path("search-box_hover.png"))
        self._search_focus = load_pixbuf(image_util.image_path("search-box_focus.png"))

        self._image = gtk.Image()
        self.add(self._image)
        self._image.set_from_pixbuf(search_normal)

        self._on_enter = lambda w, e: self._image.set_from_pixbuf(search_hover)
        self._on_leave = lambda w, e: self._image.set_from_pixbuf(search_normal)

        self._enter_notify_handler_id = None
        self._leave_notify_handler_id = None

        self.enable_roll_over()

    def _on_focus(self):
        self._image.set_from_pixbuf(self._search_focus)

    def disable_roll_over(self):
        if self._enter_notify_handler_id:
            self.disconnect(self._enter_notify_handler_id)
            self._enter_notify_handler_id = None

        if self._leave_notify_handler_id:
            self.disconnect(self._leave_notify_handler_id)
            self._leave_notify_handler_id = None

        self._on_focus()

    def enable_roll_over(self):
        if not self._enter_notify_handler_id:
            self._enter_notify_handler_id = self.connect("enter-notify-event", self._on_enter)
        if not self._leave_notify_handler_id:
            self._leave_notify_handler_id = self.connect("leave-notify-event", self._on_leave)

        self._on_leave(None, None)

class SearchBoxLabel(gtk.Label):

    def __init__(self, default_text, width, left_margin, right_padding, right_margin):
        gtk.Label.__init__(self)

        self._LEFT_MARGIN = left_margin
        self._RIGHT_MARGIN = right_margin
        self._RIGHT_PADDING = right_padding
        self._WIDTH=width

        self.set_text(default_text)
        self.set_padding(5, 3)
        self.set_justify(gtk.JUSTIFY_LEFT)
        self.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#fff'))

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

class SearchBoxButton(gtk.EventBox):

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.set_visible_window(False)
        internet_pixbuf = load_pixbuf(image_util.image_path("button_browser_google.png"))

        image = gtk.Image()
        image.set_from_pixbuf(internet_pixbuf)
        image.set_padding(10, 0)
        self.add(image)

class SearchBoxContainer(gtk.Fixed):


    def __init__(self, button, label, frame, left_margin, top_margin):
        gtk.Fixed.__init__(self)

        self.put(frame, 0, 1)
        self.put(button, 5, 3)

        alignment = gtk.Alignment(0.0, 0.5, 0.0, 0.0)
        alignment.add(label)

        self.put(alignment, left_margin, top_margin)

