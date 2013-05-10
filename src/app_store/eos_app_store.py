import gettext
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView

gettext.install('eos_app_store', '/usr/share/locale', unicode=True, names=['ngettext'])
Gdk.threads_init()

class EosAppStore(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)
        
        #width, height = self._get_net_work_area()
        #self.resize(width, height)

    def do_activate(self):
        print("do activate")
        win = AddShortcutsView(self)
        win.show_all()

    def do_startup(self):
        print ("do startup")
        Gtk.Application.do_startup(self)

    def _get_net_work_area(self):
        """this section of code gets the net available area on the window (i.e. root window - panels)"""
        self.realize()
        window = self.get_window()
        screen = window.get_screen()
        monitor = screen.get_monitor_at_window(window)
        geometry = screen.get_monitor_geometry(monitor)
        width = geometry.width
        height = geometry.height
        print ("geometry is " + str(width) + "x" + str(height))

        return width, height
