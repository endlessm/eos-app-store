from gi.repository import Gtk
from EosAppStore.eos_widgets.abstract_notifier import AbstractNotifier
from rename_widget_constants import RenameWidgetConstants

class RenameWidgetView(AbstractNotifier):
    def __init__(self, x, y, caller_width):
        self._caller_width = caller_width
        self.x = x
        self.y = y

        self._window = Gtk.Window(Gtk.WINDOW_TOPLEVEL)
        self._window.set_decorated(False)
        self._window.set_border_width(0)
        self._window.set_skip_taskbar_hint(True)

        self._text_view = Gtk.Entry()
        self._text_view.set_alignment(0.5)
        self._text_view.set_has_frame(False)
        self._text_view.set_editable(False)
        self._text_view.set_state(Gtk.STATE_SELECTED)
        self._window.add(self._text_view)
        self._text_view.connect("key-release-event", self._handle_key_press)
        self._text_view.connect("button-press-event", self._handle_click)
        self._text_view.connect("focus-out-event", self._focus_out)

    def _focus_out(self, widget, event):
        self._notify(RenameWidgetConstants.RETURN_PRESSED)

    def resize_window(self):
        t_width = self._text_view.get_layout().get_pixel_size()[0]
        if t_width <= self._caller_width:
            t_width = self._caller_width
        else:
            t_width += 5
        self._window.set_size_request(t_width, -1)
        self._window.move(self.x - (int((t_width - self._caller_width)/2)), self.y)

    def show_window(self):
        self._window.show_all()

    def set_original_name(self, name):
        self._text_view.set_text(name)
        self._text_view.select_region(0, -1)

    def _handle_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Escape':
            self._notify(RenameWidgetConstants.ESCAPE_PRESSED)
        elif Gdk.keyval_name(event.keyval) == 'Return':
            self._notify(RenameWidgetConstants.RETURN_PRESSED)

    def get_new_name(self):
        return self._text_view.get_text().strip()

    def _handle_click(self, widget, event):
        widget.set_state(Gtk.STATE_NORMAL)
        widget.set_editable(True)

    def close_window(self):
        self._window.destroy()
