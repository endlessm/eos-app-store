from desktop_layout import DesktopLayout
import gettext

import gtk
import gobject
from gtk import gdk

from shortcut.application_shortcut import ApplicationShortcut
from shortcut.folder_shortcut import FolderShortcut
from shortcut.separator_shortcut import SeparatorShortcut
from shortcut.add_remove_shortcut import AddRemoveShortcut
from folder.folder_window import OpenFolderWindow
from folder.folder_window import FULL_FOLDER_ITEMS_COUNT
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView
from eos_util.image import Image
from shortcut.desktop_shortcut import DesktopShortcut
from ui.padding_widget import PaddingWidget

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window, object):

    def __init__(self):
        gtk.Window.__init__(self)
        
        width, height = self._get_net_work_area()
        self.resize(width, height)

        add_shortcut_popup = AddShortcutsView(parent=self, width=width, height=height)
        add_shortcut_popup.show()

    def _get_net_work_area(self):
        """this section of code gets the net available area on the window (i.e. root window - panels)"""
        self.realize()
        screen = gtk.gdk.Screen() #@UndefinedVariable
        monitor = screen.get_monitor_at_window(self.window)
        geometry = screen.get_monitor_geometry(monitor)
        width = geometry.width
        height = geometry.height

        return width, height

