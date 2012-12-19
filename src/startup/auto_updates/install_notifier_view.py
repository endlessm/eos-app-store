import gtk

from ui.abstract_notifier import AbstractNotifier
from ui import glade_ui_elements

class InstallNotifierView(AbstractNotifier):
    RESTART_NOW = "restart.now"
    RESTART_LATER = "restart.later"
    
    def __init__(self):
        builder = gtk.Builder()
        builder.set_translation_domain("endless_desktop")
        builder.add_from_string(glade_ui_elements.install_notifier)

        self._window = builder.get_object("dialog_window")
        self._window.set_wmclass("eos-dialog", "Eos-dialog")
        
        self._message_label = builder.get_object("message_label")
        self._restart_button = builder.get_object("restart_button")
        self._cancel_button = builder.get_object("restart_later")
        
        self._restart_button.connect("released", lambda w: self._notify(self.RESTART_NOW))
        self._cancel_button.connect("released", lambda w: self._notify(self.RESTART_LATER))
        
    def display(self):
        self._window.show_all()

    def close(self):
        self._window.destroy()
        
    def set_new_version(self, text):
        formatted_text = _("Version {0} of EndlessOS is ready to be installed. After installation, a restart is required.  Would you like to install and restart now?").format(text)
        self._message_label.set_text(formatted_text)

