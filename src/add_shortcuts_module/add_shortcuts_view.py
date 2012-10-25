import gtk
# from util.transparent_window import TransparentWindow
from add_shortcuts_model import AddShortcutsModel
from shortcut_category_box import ShortcutCategoryBox
from add_folder_box import AddFolderBox
from shortcut.folder_shortcut import FolderShortcut
from osapps.app_shortcut import AppShortcut
from shortcut.add_remove_shortcut import AddRemoveShortcut
from util.transparent_window import TransparentWindow

class AddShortcutsView():
    def __init__(self, parent=None, add_remove_widget=None, width=0, height=0):
        self._add_buton_box_width = 120
        self._tree_view_width = 200
        
        if not width:
            self._width = parent.allocation.width
        else:
            self._width = width
        
        if not height:
            self._height = parent.allocation.height
        else:
            self._height = parent.allocation.height
            
        if not add_remove_widget:
            self._add_remove_widget = AddRemoveShortcut(callback=None)
            self._add_remove_widget.show()
        else:
            self._add_remove_widget = add_remove_widget
        
        self._parent = parent
        self._model = AddShortcutsModel()
        self.window = TransparentWindow(self._parent)
        self.window.set_title(_("Prototype"))
        self.window.set_decorated(False)
        self.window.set_size_request(self._width, self._height)
        self.window.move(0,0)
        self.window.connect("delete_event", self.destroy)
        #main hbox
        self.hbox = gtk.HBox()
        # addremoveshortcut hbox
        self.add_remove_vbox = gtk.VBox()
        self.add_remove_vbox.set_size_request(self._add_buton_box_width, self._height)
        print self.add_remove_vbox.get_size_request()
        
        self._lc = gtk.Alignment(0.5, 0.5, 0, 0)
        self._add_remove_widget.show()
        self._lc.add(self._add_remove_widget)
        self.add_remove_vbox.pack_start(self._lc)
        self.add_remove_vbox.show()
        self.hbox1 = gtk.HBox()
        self.hbox1.set_size_request(self._tree_view_width, self._height)
        self.data = self._model.get_tree_data()
        self.tree = ShortcutCategoryBox(self.data)
        self.tree.set_size_request(200, -1)
        self.left_center = gtk.Alignment(0, 0.5, 0, 0)
        self.left_center.add(self.tree)
        self.hbox1.pack_start(self.left_center)
        self.hbox2 = gtk.HBox()
        self.hbox2.set_size_request(self._width - self._tree_view_width - self._add_buton_box_width, self._height)
        print self.hbox2.get_size_request()
        # details view folder add
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.folder_box = AddFolderBox(self)
        self.scrolled_window.add_with_viewport(self.folder_box)
        self.folder_box.show()
        #scrolled_window.show_all()
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
        path = self._model.create_directory(folder_name)
        if path:
            shortcut = AppShortcut(key='', name=folder_name, icon=image_file)
            self._parent.get_presenter()._model._app_desktop_datastore.add_shortcut(shortcut)