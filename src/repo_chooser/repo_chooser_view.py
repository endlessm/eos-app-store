import gtk
from gtk import gdk #@UnusedImport

from ui.abstract_notifier import AbstractNotifier

class RepoChooserView(AbstractNotifier):
    _MESSAGE_TEMPLATE = "Would you like to begin the Endless OS %supdate now?"
    SECRET_KEY_COMBO_PRESSED = "secret.key.combo.pressed"
    PASSWORD_ENTERED = "password.entered"
    UPDATE_RESPONSE = "update.response"

    def __init__(self):
        self._update_dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Welcome to the EndlessOS installer.")
        self._update_dialog.set_position(gtk.WIN_POS_CENTER)
        self._update_dialog.set_modal(True)
        
        # TODO internationalize
        self._update_dialog.set_title("EndlessOS Installer")
        
        self._update_dialog.set_wmclass("eos-dialog", "Eos-dialog")
        self._update_dialog.connect("key_press_event", self._key_press_handler)
        self._update_dialog.connect("response", self._handle_update_response)

    def display(self):
        self._update_dialog.show_all()

    def _handle_update_response(self, dialog, response_id):
        self._update_response = response_id
        self._notify(self.UPDATE_RESPONSE)
        
    def close_update_dialog(self):
        self._update_dialog.destroy()

    def get_update_response(self):
        return self._update_response == gtk.RESPONSE_YES

    def _key_press_handler(self, widget, event):
        if event.state & gdk.CONTROL_MASK:
            if event.state & gdk.SHIFT_MASK:
                if gdk.keyval_name(event.keyval).lower() == "e": #@UndefinedVariable
                    self._notify(self.SECRET_KEY_COMBO_PRESSED)

    def set_repo_name(self, repo_name):
        self._update_dialog.format_secondary_text(self._MESSAGE_TEMPLATE % repo_name)
            
    def prompt_for_password(self):
        self._password_prompt_dialog = gtk.Dialog("Choose Repository", self._update_dialog,  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self._password_prompt_dialog.set_wmclass("eos-dialog", "Eos-dialog")
        self._password_prompt_dialog.set_default_response(gtk.RESPONSE_ACCEPT)
  
        label = gtk.Label("Password:")
        self._entry = gtk.Entry()
        self._entry.set_activates_default(True)
        self._entry.set_visibility(False)
        
        hbox = gtk.HBox(False, 2)
        hbox.pack_start(label)
        hbox.pack_end(self._entry)
        self._password_prompt_dialog.vbox.pack_start(hbox)
        self._password_prompt_dialog.show_all()

        self._password_prompt_dialog.connect("response", self._notify_password_response)

    def _notify_password_response(self, dialog, response_id):
        self._password_dialog_response = response_id
        self._notify(self.PASSWORD_ENTERED)

    def close_password_dialog(self):
        self._password_prompt_dialog.destroy()

    def get_password_response(self):
        return self._password_dialog_response == gtk.RESPONSE_ACCEPT

    def get_password(self):
        return self._entry.get_text()
        
    def inform_user_of_update(self):
        info_message = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, 
                _("Downloading updates to the EndlessOS. We will notify you once the updates are ready to install."))
        info_message.connect("response", lambda w, id: info_message.destroy())
        info_message.show()

