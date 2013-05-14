import gettext
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView

gettext.install('eos_app_store', '/usr/share/locale', unicode=True, names=['ngettext'])
class EosAppStore(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        win = AddShortcutsView(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)
