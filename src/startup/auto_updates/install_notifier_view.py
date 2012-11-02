import gtk
import gettext

from ui.abstract_notifier import AbstractNotifier
from ui import glade_ui_elements

gettext.install("endless_desktop", "/usr/share/locale", unicode=True, names=["ngettext"])

class InstallNotifierView(AbstractNotifier):
    RESPONSE_EVENT = "response_event"
    
    def __init__(self):
        builder = gtk.Builder()
        builder.set_translation_domain("endless_desktop")
        builder.add_from_string(glade_ui_elements.install_notifier)

        self._window = builder.get_object("dialog_window")
        self._window.set_wmclass("eos-dialog", "Eos-dialog")
        self._window.connect('response', lambda w, e: self._notify(self.RESPONSE_EVENT))

    def display(self):
        self._window.show_all()

    def close_dialog(self):
        self._window.destroy()

