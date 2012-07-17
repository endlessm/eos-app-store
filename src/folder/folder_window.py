import gtk
import gettext
from util.image_eventbox import ImageEventBox
from util import image_util, screen_util
from util.transparent_window import TransparentWindow
from folder.folder_icons import FolderIcons

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class OpenFolderWindow():
    TASKBAR_HEIGHT = 40
    
    def __init__(self, parent_window, callback, shortcut):
        self._width = screen_util.get_width()
        # TODO fix this
        self._height = 116
        
        self._window = TransparentWindow()
        self._window.set_title(_("Folder"))
        
        self._window.set_parent_window(parent_window)
#        self._window.set_gravity(gtk.gdk.GRAVITY_SOUTH_WEST)
#        self._window.move(0, 0)
        self._window.move(0, screen_util.get_height() - self._height - self.TASKBAR_HEIGHT)

        self._fancy_container = ImageEventBox((image_util.image_path("open-folder-bg.png"),), self._width)
        self._fancy_container.show()
        

        self._fancy_container.set_size_request(self._width,self._height)
        self._window.set_size_request(self._width,self._height)
        
        self._center = gtk.Alignment(.5,0.1,0,0)
        self._center.show()
        
        self._container = gtk.HBox(False)
        
        print "children", shortcut.get_children_ids()
        folder_icons = FolderIcons(shortcut.get_children())
        self._container.pack_start(folder_icons, False, False, 0)
        folder_icons.connect("application-shortcut-activate", lambda w, app_id: callback(app_id))
        
        self._center.add(self._container)
        self._fancy_container.add(self._center)

        self._window.add(self._fancy_container)
        self._window.show()
        

    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
