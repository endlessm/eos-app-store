import gtk
from add_shortcuts_presenter import AddShortcutsPresenter
from shortcut_category_box import ShortcutCategoryBox
from add_folder_box import AddFolderBox
from shortcut.add_remove_shortcut import AddRemoveShortcut
from util.transparent_window import TransparentWindow
from osapps.app_shortcut import AppShortcut
import cairo
from eos_util import image_util

class AddShortcutsView():
    def __init__(self, parent=None, add_remove_widget=None, width=0, height=0):
        self._add_buton_box_width = 120
        self._tree_view_width = 214

        self._width = width or parent.allocation.width
        self._height = height or parent.allocation.height

        if not add_remove_widget:
            self._add_remove_widget = AddRemoveShortcut(callback=None)
            self._add_remove_widget.show()
        else:
            self._add_remove_widget = add_remove_widget

        self._parent = parent
        self._presenter = AddShortcutsPresenter()
        self.window = TransparentWindow(self._parent)
        self.window.set_title(_("Add Shortcuts"))
        self.window.set_decorated(False)
        self.window.set_size_request(self._width, self._height)
        self.window.move(0,0)
        self.window.connect("delete_event", self.destroy)
        self.window.connect("expose-event", self._draw_triangle)

        self.hbox = gtk.HBox()
        self.add_remove_vbox = gtk.VBox()
        self.add_remove_vbox.set_size_request(self._add_buton_box_width, self._height)

        self._lc = gtk.Alignment(0.5, 0.5, 0, 0)
        self._add_remove_widget.show()
        self._lc.add(self._add_remove_widget)

        self.add_remove_vbox.pack_start(self._lc)
        self.add_remove_vbox.show()
        self.hbox1 = gtk.HBox()
        self.hbox1.set_size_request(self._tree_view_width, self._height)

        self.data = self._presenter.get_category_data()
        self.tree = ShortcutCategoryBox(self.data, self.window, self._tree_view_width)

        self.hbox1.pack_start(self.tree)
        self.hbox2 = gtk.HBox()
        self.hbox2.set_size_request(self._width - self._tree_view_width - self._add_buton_box_width, self._height)

        self.scrolled_window = AddFolderBox(self)
        self.hbox2.pack_start(self.scrolled_window)
        self.scrolled_window.show()
        self.hbox.pack_start(self.add_remove_vbox)
        self.hbox.pack_start(self.hbox1)
        self.hbox.pack_end(self.hbox2)
        self.window.add(self.hbox)
        self.show()

    def show(self):
        self.window.show_all()


    def destroy(self, window, event):
        self.window.destroy()
        self._parent.get_presenter().refresh_view()


    def create_folder(self, folder_name, image_file):
        presenter = self._parent.get_presenter()
        self._presenter.create_directory(folder_name, image_file, presenter)

    def _draw_triangle(self, widget, event):
        ctx = self.add_remove_vbox.window.cairo_create()
        image_surface = cairo.ImageSurface.create_from_png(image_util.image_path("inactive_triangle.png"))
        x = self.add_remove_vbox.allocation.width - image_surface.get_width()
        y = int(self.add_remove_vbox.allocation.height/2 - image_surface.get_height()/2) + 1
        ctx.save()
        ctx.translate(x, y)
        ctx.set_source_surface(image_surface)
        ctx.paint()
        ctx.restore()
