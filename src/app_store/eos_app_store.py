import gettext
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView

gettext.install('eos_app_store', '/usr/share/locale', unicode=True, names=['ngettext'])
Gdk.threads_init()

class EosAppStore(Gtk.Window, object):

    def __init__(self):
        Gtk.Window.__init__(self)
        
        width, height = self._get_net_work_area()
        self.resize(width, height)

        add_shortcut_popup = AddShortcutsView(parent=self, width=width, height=height)
        add_shortcut_popup.show()

    def _get_net_work_area(self):
        """this section of code gets the net available area on the window (i.e. root window - panels)"""
        self.realize()
        screen = Gdk.Screen() #@UndefinedVariable
        #monitor = screen.get_monitor_at_window(Gdk.Window)
        #geometry = screen.get_monitor_geometry(monitor)
        #width = geometry.width
        #height = geometry.height
	height=600
	width=800

        return width, height
