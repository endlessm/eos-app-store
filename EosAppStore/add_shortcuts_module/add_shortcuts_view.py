from gi.repository import Gtk
from gi.repository import GLib

import gettext

from add_shortcuts_presenter import AddShortcutsPresenter
from shortcut_category_box import ShortcutCategoryBox
from add_folder_box import AddFolderBox
from add_application_box import AddApplicationBox
from EosAppStore.eos_widgets.desktop_transparent_window import DesktopTransparentWindow
from EosAppStore.shortcut.add_remove_shortcut import AddRemoveShortcut
from add_website_box import AddWebsiteBox
import cairo
from EosAppStore.eos_util import image_util
from EosAppStore.eos_util import screen_util

import sys
import gc

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class AddShortcutsView(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, title="Application Store", application=app)
        self.set_app_paintable(True)

        self._add_button_box_width = 120
        self._tree_view_width = 214

        # Hardcode size. Not a real problem, as application will run maximized
        self._width = 640
        self._height = 480
        self.set_default_size(self._width, self._height)

        self._add_remove_widget = AddRemoveShortcut(callback=lambda a, b:False)
        self._presenter = AddShortcutsPresenter(view=self)
        self.data = self._presenter.get_category_data()
        self.tree = ShortcutCategoryBox(self.data, self, self._tree_view_width, self._presenter)

        self._lc = Gtk.Alignment()
        self._lc.set(0.5,0.5,0,0)
        self._lc.add(self._add_remove_widget)

        self.add_remove_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add_remove_vbox.set_size_request(self._add_button_box_width, self._height)
        self.add_remove_vbox.pack_start(self._lc, True, True, 0)

        self.event_box = Gtk.EventBox()
        self.event_box.set_visible_window(False)
        self.event_box.connect('button-press-event', self.destroy)
        self.event_box.uat_id = 'close_app_store'
        self.event_box.uat_offset = (0, -50)
        self.event_box.add(self.add_remove_vbox)

        self.hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox1.set_size_request(self._tree_view_width, self._height)
        self.hbox1.pack_start(self.tree, True, False, 0)

        self.hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox2.set_homogeneous(False)
        self.hbox2.set_size_request(self._width - self._tree_view_width - self._add_button_box_width, self._height)
        self.scrolled_window = AddApplicationBox(self, self._presenter, screen_util.get_width(self), screen_util.get_height(self))
        self.hbox2.pack_start(self.scrolled_window, True, True, 0)

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox.pack_start(self.event_box, False, True, 0)
        self.hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox.pack_end(self.hbox2, True, True, 0)

        self.add(self.hbox)

        self.connect("delete-event", self.destroy)
        self.connect("draw", self._draw_triangle)

        self.maximize()
        self.show_all()

        return

        self._add_remove_widget.show()
        self.add_remove_vbox.show()

        #self.tree = ShortcutCategoryBox(self.data, self.window, self._tree_view_width, self._presenter)

        self.scrolled_window.show()
        #self.window.add(self.hbox)
        self.show_all()

        # screen = win.get_screen()
        # visual = screen.get_rgba_visual()
        # if not visual:
        #     visual = screen.get_system_visual()

        #win.set_visual(visual)

    @property
    def add_button_box_width(self):
        return self._add_button_box_width

    @property
    def tree_view_width(self):
        return self._tree_view_width

    def show(self):
        self.window.show_all()

    def destroy(self, window, event):
        self.close()

    def close(self):
        Gtk.ApplicationWindow.destroy(self)
        
    def create_folder(self, folder_name, image_file):
        self._presenter.install_folder(folder_name);

    def install_app(self, application_model):
        shortcut = self._presenter.build_shortcut_from_application_model(application_model)
        self._presenter.install_app(application_model)
        self.install_shortcut(shortcut)

    def install_site(self, link_model):
        shortcut = self._presenter.build_shortcut_from_link_model(link_model)
        self._presenter.install_app(link_model)
        self.install_shortcut(shortcut)

    def install_shortcut(self, shortcut):
        self._presenter.add_shortcut(shortcut)
    
    def _draw_triangle(self, widget, cr):
        ctx = self.add_remove_vbox.get_window().cairo_create()
        image_surface = cairo.ImageSurface.create_from_png(image_util.image_path("inactive_triangle.png"))
        x = self.add_remove_vbox.get_allocation().width - image_surface.get_width()
        y = int(self.add_remove_vbox.get_allocation().height/2 - image_surface.get_height()/2) + 1
        ctx.save()
        ctx.translate(x, y)
        ctx.set_source_surface(image_surface)
        ctx.paint()
        ctx.restore()

    def set_scrolled_window(self, widget):
        old_widget = self.hbox2.get_children()[0]
        self.hbox2.remove(old_widget)
        old_widget.destroy()

        self.scrolled_window = widget
        self.hbox2.pack_start(self.scrolled_window, True, True, 0)
        self.scrolled_window.show()

    def set_add_shortcuts_box(self, category, subcategory=''):
        if category == _('APP'):
            widget = AddApplicationBox(self, self._presenter, screen_util.get_width(self), screen_util.get_height(self), default_category=subcategory)
        elif category == _('WEB'):
            widget = AddWebsiteBox(self)
        else:
            widget = AddFolderBox(self)

        self.set_scrolled_window(widget)

