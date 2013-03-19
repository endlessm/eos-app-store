import gtk
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from eos_util import image_util 


class WebsiteRowBox(gtk.EventBox):
    def __init__(self, item=None, parent=None, presenter=None, desktop_preference_class = DesktopPreferencesDatastore):
        super(WebsiteRowBox, self).__init__()
        self.set_visible_window(False)
        self._link_model = item
        self._parent = parent
        self._presenter = presenter
        self._id = item._id
        self._name = self._link_model._name
        self._description = self._link_model._comment
        self._icon_image_width = 32
        self._icon_image_height = 32
        self._default_icon_pixbuf = image_util.load_pixbuf(image_util.image_path("endless-browser.png"))
        self._icon_pixbuf = image_util.load_pixbuf(image_util.image_path(self._link_model.normal_icon()))
        self._height = 60
        self._plus_offset_for_scrollbar = 30

        # The current implementation of get_favicon is way too slow,
        # as it retrieves data from each site at run-time
        # For now, let's just use a default icon
        #self._icon_image = self._presenter.get_favicon(self._link_model._url) or self._default_icon_pixbuf
        self._icon_image = self._icon_pixbuf or self._default_icon_pixbuf

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
        if not (self._icon_image.get_width() == self._icon_image_width and self._icon_image.get_height() == self._icon_image_height):
            self._icon_image = self._icon_image.scale_simple(self._icon_image_width, self._icon_image_height, gtk.gdk.INTERP_BILINEAR)
        self.icon_image_box.set_from_pixbuf(self._icon_image)
        self.icon_alignment.add(self.icon_image_box)

        #textual data
        self.name_label = gtk.Label()
        self.name_label.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold">' + self._name + '</span>')
        self.name_label.set_alignment(0, 0.5)
        self.description_label = gtk.Label()
        self.description_label.set_markup('<span color="#aaaaaa" font-style="italic">' + self._link_model._url + '</span>')
        self.description_label.set_alignment(0,0.5)
        
        self.labels_box = gtk.HBox()
        self.labels_box.pack_start(self.name_label, False, False, 20)
        self.labels_box.pack_start(self.description_label, False, False, 20)
        
        # This is a hack!
        # If no size request is set, the plus icon is displayed half off the edge,
        # at least on a 1366x768 laptop monitor.  By setting any size request,
        # even though the size request seems to be ignored in terms of the size of the
        # labels box, the plus icon appears in the correct location.
        # TODO Consider how to fix for appropriate sizing based on screen size
        self.labels_box.set_size_request(1, 1)

        #place for displaying + icon
        self._plus_box_alignment = gtk.Alignment(0.5, 0.5, 0, 0)
        self._plus_box_alignment.set_size_request(self._plus_box_width + self._plus_offset_for_scrollbar,
                                                  self._height - 2)
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
        self.connect("button-release-event", self.install_site)

        self.show_all()
        
    def install_site(self, widget, event):
        self._parent.install_site(self._link_model)
