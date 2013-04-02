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
from taskbar_panel.taskbar_panel import TaskbarPanel
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView
from eos_util.image import Image
from shortcut.desktop_shortcut import DesktopShortcut
from desktop_page.desktop_page_view import DesktopPageView
from search.search_box import SearchBox
from desktop.base_desktop import BaseDesktop
from desktop_nav_button import DesktopNavButton
from ui.padding_widget import PaddingWidget
from desktop_page.button import Button

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window, object):
    _app_shortcuts = {}

    def __init__(self):
        gtk.Window.__init__(self)
        
        width, height = self._get_net_work_area()
        self.resize(width, height)

        self.set_app_paintable(True)
        self.set_can_focus(False)
        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DESKTOP) #@UndefinedVariable
        self.set_decorated(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.connect('button-press-event', self.unfocus_widget)
        self.connect('destroy', lambda w: gtk.main_quit())
        self.maximize()

        add_shortcut_popup = AddShortcutsView(parent=self, width=width, height=height)
        add_shortcut_popup.show()


    def unfocus_widget(self, widget, event):
        widget.set_focus(None)
        self.close_folder_window()

    def set_presenter(self, presenter):
        self._presenter = presenter

    def get_presenter(self):
        return self._presenter

    def set_background_image(self, image):
        width, height = self._get_net_work_area()
        image.scale_to_best_fit(width, height)
        
        pixmap = image.pixbuf.render_pixmap_and_mask()[0]
        self.window.set_back_pixmap(pixmap, False)

        self.window.invalidate_rect((0, 0, width, height), False)

    def desktop_page_navigate(self, index):
        self._presenter.desktop_page_navigate(index + 1)

    def hide_folder_window(self):
        if hasattr(self, '_folder_window') and self._folder_window:
            self._folder_window.hide()

    def close_folder_window(self):
        if hasattr(self, '_folder_window') and self._folder_window:
            self._folder_window.destroy()
            self._folder_window = None

    def show_folder_window(self, shortcut):
        self.close_folder_window()
        self._folder_window = OpenFolderWindow(
            self,
            self._presenter.activate_item,
            shortcut,
            self._dnd_begin
            )
        self._folder_window.show()

    def show_folder_window_by_name(self, shortcut_name):
        shortcut = self._presenter.get_shortcut_by_name(shortcut_name)
        if shortcut is not None:
            self.show_folder_window(shortcut)

    def _get_net_work_area(self):
        """this section of code gets the net available area on the window (i.e. root window - panels)"""
        self.realize()
        screen = gtk.gdk.Screen() #@UndefinedVariable
        monitor = screen.get_monitor_at_window(self.window)
        geometry = screen.get_monitor_geometry(monitor)
        width = geometry.width
        height = geometry.height

        return width, height

    def show_add_dialogue(self, event_box, event):
        add_shortcut_popup = AddShortcutsView(parent=self)
        add_shortcut_popup.show()

