import gtk
from add_shortcuts_presenter import AddShortcutsPresenter
from shortcut_category_box import ShortcutCategoryBox
from add_folder_box import AddFolderBox
from add_application_box import AddApplicationBox
from shortcut.add_remove_shortcut import AddRemoveShortcut
from eos_widgets.desktop_transparent_window import DesktopTransparentWindow
from add_website_box import AddWebsiteBox
import cairo
from eos_util import image_util

class AddShortcutsView():
    def __init__(self, parent=None, add_remove_widget=None, width=0, height=0):
        self._add_button_box_width = 120
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
        self._presenter.set_add_shortcuts_view(self)
        self.window = DesktopTransparentWindow(self._parent, (0, 0), (self._width, self._height))
        self.window.connect("delete_event", self.destroy)
        self.window.connect("expose-event", self._draw_triangle)

        self.hbox = gtk.HBox()
        self.add_remove_vbox = gtk.VBox()
        self.add_remove_vbox.set_size_request(self._add_button_box_width, self._height)

        self._lc = gtk.Alignment(0.5, 0.5, 0, 0)
        self._add_remove_widget.show()
        self._lc.add(self._add_remove_widget)

        self.add_remove_vbox.pack_start(self._lc)
        self.add_remove_vbox.show()
        self.hbox1 = gtk.HBox()
        self.hbox1.set_size_request(self._tree_view_width, self._height)

        self.data = self._presenter.get_category_data()
        self.tree = ShortcutCategoryBox(self.data, self.window, self._tree_view_width, self._presenter)

        self.hbox1.pack_start(self.tree)
        self.hbox2 = gtk.HBox()
        self.hbox2.set_size_request(self._width - self._tree_view_width - self._add_button_box_width, self._height)
        
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
    
    def install_app(self, app):
        presenter = self._parent.get_presenter()
        shortcut = self._presenter.install_app(app)
        presenter._model._app_desktop_datastore.add_shortcut(shortcut)
    
    def install_site(self, site):
        presenter = self._parent.get_presenter()
        shortcut = self._presenter.install_site(site)
        presenter._model._app_desktop_datastore.add_shortcut(shortcut)
    
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
    
    def set_scrolled_window(self, widget):
        self.hbox2.remove(self.hbox2.get_children()[0])
        self.scrolled_window = widget
        self.hbox2.pack_start(self.scrolled_window)        
        self.scrolled_window.show()
    
    def set_add_shortcuts_box(self, category, subcategory=''):
        if category == _('APP'):
            widget = AddApplicationBox(self, default_category=subcategory)
        elif category == _('WEB'):
            widget = AddWebsiteBox(self)
        else:
            widget = AddFolderBox(self)
        
        self.set_scrolled_window(widget)
    
    def set_presenter(self, presenter):
        self._presenter = presenter