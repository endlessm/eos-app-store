import gtk
import gettext
from eos_widgets.folder_eventbox import FolderEventBox
from eos_util.image import Image
from eos_util import screen_util
from eos_widgets.transparent_window import TransparentWindow
from folder.folder_icons import FolderIcons

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

FULL_FOLDER_ITEMS_COUNT = 21
MAX_ITEMS_IN_ROW = 7
WIDGET_HEIGHT = 64
WIDGET_WIDTH = 64
WIDGET_LABEL_HEIGHT = 20
WIDGET_VERTICAL_SPACING = 64
WIDGET_HORIZONTAL_SPACING = 64
class OpenFolderWindow():
    TASKBAR_HEIGHT = 60
    
    def __init__(self, parent, callback, shortcut, hide_callback):

        self._container = gtk.VBox(
            homogeneous=False, 
            spacing=WIDGET_VERTICAL_SPACING
            )
        
        rows = []
        row_items = []
        for child in shortcut.children():
            if len(row_items) >= MAX_ITEMS_IN_ROW:
                rows.append(row_items)
                row_items = []
            row_items.append(child)
        rows.append(row_items)
                
        for row in rows:
            folder_icons = FolderIcons(row, WIDGET_HORIZONTAL_SPACING)
            self._container.pack_start(
                folder_icons, 
                expand = False, 
                fill = False, 
                padding = 0
                )
            folder_icons.connect(
                "application-shortcut-activate", 
                lambda w, app_id, params: callback(app_id, params)
                )
            
            folder_icons.connect(
                "desktop-shortcut-dnd-begin", 
                lambda w: hide_callback(w)
                )

        image = Image.from_name("open-folder-bg.png")
        
        desktop_size = parent.get_size()
        self._x = 0
        self._y = desktop_size[1] - image.height - self.TASKBAR_HEIGHT
        self._width = desktop_size[0]
        self._height = image.height

        # TODO Complete support for multiple rows of icons in folder.
        # The following line appears to account for the possibility
        # of multiple rows of icons in the folder,
        # but I don't see the image being stretched to this height,
        # so for now I'm going to comment it out and just use the image height.
        # self._height = len(rows) * (WIDGET_HEIGHT + WIDGET_LABEL_HEIGHT + WIDGET_VERTICAL_SPACING)
        
        self._window = TransparentWindow(parent, (self._x, self._y), (self._width, self._height), gradient_type='linear')

        self._fancy_container = FolderEventBox(image, self._width)
        self._fancy_container.show()
        
        self._window.set_size_request(self._width, self._height)
        
        self._center = gtk.Alignment(.5,0.1,0,0)
        self._center.show()
        self._center.add(self._container)

        self._window.add(self._center)
        self._window.show()
        

    def show(self):
        self._window.show_all()
        
    def hide(self):
        self._window.hide()
        
    def destroy(self):
        self._window.destroy()
