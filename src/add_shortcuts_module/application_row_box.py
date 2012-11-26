import gtk
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from eos_util import image_util
from xdg.DesktopEntry import DesktopEntry
from application_store.application_model import ApplicationModel 


class ApplicationRowBox(gtk.EventBox):
    def __init__(self, item=None, parent=None, presenter=None, desktop_preference_class = DesktopPreferencesDatastore):
        super(ApplicationRowBox, self).__init__()
        self.set_visible_window(False)
        self._item = item
        self._desktop_file_path = self._item._desktop_file_path
        de = DesktopEntry()
        de.parse(self._desktop_file_path)
        self._desktop_entry = de
        self._parent = parent
        self._presenter = presenter
        self._id = item._id
        self._name = self._desktop_entry.getName()
        self._description = self._desktop_entry.getComment()
        self._type = self._desktop_entry.getType()
        self._icon_image_width = 48
        self._icon_image_height = 48
        self._default_icon = image_util.image_path("endless.png")
        self._height = 80
        
        self._icon_image = self._desktop_entry.get('X-EndlessM-Normal-Icon') or self._default_icon
        
        self._icon_width = 150
        self._plus_box_width = 80
        
        # -- DISPLAY ELEMENTS
        self._vbox = gtk.VBox()
        self._top_active_line = gtk.Image()
        self._top_active_line.set_size_request(-1, 1)
        self._bottom_active_line = gtk.Image()
        self._bottom_active_line.set_size_request(-1, 1)
        self._row = gtk.HBox()
        
        # icon
        self.icon_alignment = gtk.Alignment(0.5, 0.5, 0, 0)
        self.icon_alignment.set_size_request(self._icon_width, self._height-2)
        self.icon_image_box = gtk.Image()
        self.icon_image_box.set_size_request(self._icon_image_width, self._icon_image_height)
        self.icon_image_box.set_from_file(self._icon_image)
        self.icon_alignment.add(self.icon_image_box)

        #textual data
        self.name_label = gtk.Label()
        self.name_label.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold">' + self._name + '</span>')
        self.name_label.set_alignment(0, 0.5)
        self.description_label = gtk.Label()
        self.description_label.set_markup('<span color="#aaaaaa" font-style="italic">' + self._description + '</span>')
        self.description_label.set_alignment(0,0.5)
        
        self.labels_box = gtk.VBox()
        self.labels_box.pack_start(self.name_label)
        self.labels_box.pack_start(self.description_label)

        #place for displaying + icon
        self._plus_box_alignment = gtk.Alignment(0.5, 0.5, 0, 0)
        self._plus_box_alignment.set_size_request(self._plus_box_width, self._height-2)
        self._plus_image = gtk.Image()
        self._plus_box_alignment.add(self._plus_image)
        
        #pack it all
        self._row.pack_start(self.icon_alignment, False, False, 0)
        self._row.pack_start(self.labels_box, True, True, 0)
        self._row.pack_start(self._plus_box_alignment, False, False, 0)
        self._vbox.pack_start(self._top_active_line, False, False, 0)
        self._vbox.pack_start(self._row, False, False, 0)
        self._vbox.pack_start(self._bottom_active_line, False, False, 0)
        self.add(self._vbox)
        self.connect("button-release-event", self.install_app)

        self.show_all()
        
    def install_app(self, widget, event):
        self._parent.install_app(self._item)
    