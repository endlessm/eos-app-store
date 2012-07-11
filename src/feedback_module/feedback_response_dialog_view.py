import gtk
import gettext

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class FeedbackResponseDialogView():
    def __init__(self):
        self._label = gtk.Label(_("Thank you for your feedback."))
        self._dialog = gtk.Dialog(_("Thank You"))
        self._dialog.vbox.pack_start(self._label)
        self._dialog.set_position(gtk.WIN_POS_CENTER)
        self._label.show()
        
    def show(self):
        self._dialog.show_all()
    
    def destroy(self):
        self._dialog.destroy()