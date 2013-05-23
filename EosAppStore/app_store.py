import gettext
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from EosAppStore.add_shortcuts_module.add_shortcuts_view import AddShortcutsView

gettext.install('eos_app_store', '/usr/share/locale', unicode=True, names=['ngettext'])
class EosAppStore(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="com.endlessm.eos_app_store")
        self._win = None

    def do_activate(self):
        if not self._win:
            self._win = AddShortcutsView(self)
            self._win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)
