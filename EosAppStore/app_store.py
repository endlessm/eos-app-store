import gettext
import os
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from EosAppStore.add_shortcuts_module.add_shortcuts_view import AddShortcutsView
from EosAppStore.eos_util import path_util

gettext.install('eos_app_store', '/usr/share/locale', unicode=True, names=['ngettext'])
class EosAppStore(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="com.endlessm.eos_app_store")
        self._win = None

    def do_activate(self):
        if not self._win:
            provider = Gtk.CssProvider()
            provider.load_from_path(os.path.join(path_util.CSS_DIRECTORY, 'eos-app-store.css'))

            self._win = AddShortcutsView(self)

            context = Gtk.StyleContext()
            context.add_provider_for_screen(self._win.get_screen(),
                                            provider,
                                            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            self._win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)
