import gtk
import gettext
from eos_widgets.desktop_transparent_window import DesktopTransparentWindow
from folder.folder_icons import FolderIcons

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

FULL_FOLDER_ITEMS_COUNT = 21
MAX_ITEMS_IN_ROW = 7
WIDGET_HEIGHT = 64
WIDGET_WIDTH = 64
WIDGET_LABEL_HEIGHT = 20
WIDGET_VERTICAL_SPACING = 64
# Note: icon width is 64 within a box of width 112
WIDGET_HORIZONTAL_SPACING = 2 * 64 - 112
WIDGET_PADDING = 20

class OpenFolderWindow():
    
    def __init__(self, parent, callback, shortcut, hide_callback):
        self._parent = parent

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
            
            folder_icons.connect(
                "desktop-shortcut-rename", 
                lambda w, new_name, real_w: self._parent._rename_callback(real_w, new_name)
                )

        desktop_size = parent.get_size()
        self._width = desktop_size[0]
        self._height = len(rows) * WIDGET_HEIGHT + (len(rows) - 1) * WIDGET_VERTICAL_SPACING + WIDGET_LABEL_HEIGHT + WIDGET_PADDING
        
        self._x = 0
        self._y = desktop_size[1] - self._height

        self._window = DesktopTransparentWindow(parent, (self._x, self._y), (self._width, self._height), gradient_type='linear')

        # When support for multiple rows was added,
        # the image was ignored and replaced with a simple gradient.
        # This slightly changes the look of the open folder window.
        # TODO Is the current gradient per the design,
        # or does the fancy container capability below
        # need to be merged into the current capability?
        # image = Image.from_name("open-folder-bg.png")
        # self._fancy_container = FolderEventBox(image, self._width)
        # self._fancy_container.show()
        
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
