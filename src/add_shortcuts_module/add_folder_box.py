import gtk
import cairo
from eos_widgets.image_eventbox import ImageEventBox
from eos_util.image import Image
from eos_util import screen_util
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore

class AddFolderBox(gtk.VBox):

    def __init__(self, parent, add_remove_widget=None, desktop_preference_class = DesktopPreferencesDatastore):
        super(AddFolderBox, self).__init__()

        self._parent = parent

        self._ENDLESS_ICON_PATH = '/usr/share/endlessm/icons/apps/'
        # For now, hard-code the names of the Endless-designed folder icons,
        # since they are mixed in the same directory as the apps and websites,
        # and don't start with a common 'folder' prefix
        self._ENDLESS_ICON_NAMES = ['media', 'games', 'social', 'work', 'news', 'curiosity']
        self._DEFAULT_ICON_PATH = '/usr/share/icons/Humanity/places/48/'

        self._desktop_preferences = desktop_preference_class.get_instance()
        # TODO should not rely on access to private member _parent of parent
        # Is there a better way to get access to the desktop window for its size?
        self._background = self._desktop_preferences.get_scaled_background_image(
                screen_util.get_width(parent._parent),
                screen_util.get_height(parent._parent)).copy()

        self._viewport = gtk.Viewport()
        self._viewport.set_shadow_type(gtk.SHADOW_NONE)
        self._vbox = gtk.VBox()
        self._vbox.set_homogeneous(False)
        self._vbox.set_spacing(15)
        self._vbox.connect("expose-event", self._handle_event)

        label_1_text = _('1. NAME YOUR FOLDER')
        self._label_1 = gtk.Label()
        label_2_text = _('2. PICK A SYMBOL')
        self._label_2 = gtk.Label()
        self._label_1.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold" size="16000">' + label_1_text + '</span>')
        self._label_2.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold" size="16000">' + label_2_text + '</span>')

        self._text_entry_align = gtk.Alignment(0.5, 0.5, 0, 0)
        self._hbox = gtk.HBox()
        self._hbox.set_size_request(186, 24)
        self._text_entry = gtk.Entry(50)
        self._text_entry.set_alignment(0.5)
        self._hbox.pack_start(self._text_entry)
        self._text_entry.set_text('')
        self._text_entry_align.add(self._hbox)


        self.hbox_separator = gtk.HBox()
        self.hbox_separator.set_size_request(-1, 15)
        self._vbox.pack_start(self.hbox_separator, True, True, 0)
        self._vbox.pack_start(self._label_1, True, True, 0)
        self._vbox.pack_start(self._text_entry_align, False, False, 0)
        self.hbox_separator1 = gtk.HBox()
        self.hbox_separator1.set_size_request(-1, 15)
        self.hbox_separator1.connect("expose-event", self._draw_divider_line)
        self._vbox.pack_start(self.hbox_separator1)
        self._vbox.pack_start(self._label_2, True, True, 0)

        self._fill_table()

        self._table.show()
        self._bottom_center = gtk.Alignment(0.5, 0, 0, 0)
        self._bottom_center.add(self._table)
        self._vbox.pack_start(self._bottom_center)
        self._viewport.add(self._vbox)
        self.add(self._viewport)

        self.x = 0
        self.y = 0

        self.show_all()

    def _get_folder_icons(self, path='', hint='folder', suffix=''):
        return self._parent._presenter.get_folder_icons(path, hint, suffix)

    def get_images(self, image_path):
        return (
            Image.from_name("endless-shortcut-well.png"),
            Image.from_name(image_path),
            Image.from_name("endless-shortcut-foreground.png")
            )

    def _display_plus(self, widget, event, add_remove_widget):
        images_tuple = widget._images
        images_list = list(images_tuple)
        images_list.append(Image.from_name("add_folder_icon.png"))
        widget.set_images(tuple(images_list))
        widget.hide()
        widget.show()
        add_remove_widget._event_box.set_images(images_tuple)
        add_remove_widget._label.set_text(self._text_entry.get_text())
        add_remove_widget.hide()
        add_remove_widget.show()

    def _remove_plus(self, widget, event, add_remove_widget):
        images = list(widget._images)
        widget.set_images(tuple(images[:-1]))
        widget.hide()
        widget.show()
        add_remove_widget._event_box.set_images(add_remove_widget.get_images('normal'))
        add_remove_widget._label.set_text('')
        add_remove_widget.hide()
        add_remove_widget.show()

    def _create_folder(self, widget, event, image_file):
        if self._text_entry.get_text() != 'Untitled' and self._text_entry.get_text():
            self._parent.create_folder(self._text_entry.get_text(), image_file)
            self._parent.destroy(None, None)
        else:
            print 'FOLDER MUST HAVE A NAME!'

    def _handle_event(self, widget, event):
        cr = widget.window.cairo_create()

        if self.x == 0 and self.y == 0:
            x, y = self._vbox.window.get_origin()
            top_x, top_y = self._vbox.window.get_toplevel().get_origin()
            self.x = x - top_x
            self.y = y - top_y
            self._background.crop(self.x, self.y, event.area.width, event.area.height)

        self.draw(cr, event.area.x, event.area.y, event.area.width, event.area.height)

        return False

    def draw(self, cr, x, y, w, h):
        cropped_background = self._background.copy().crop(x, y, w, h)
        cropped_background.draw(lambda pixbuf: cr.set_source_pixbuf(pixbuf, x, y))
        cr.paint()
        self._draw_gradient(cr, x, y, w, h)

    def _draw_gradient(self, cr, x, y, w, h):
        # TODO This is not quite appropriate when drawing the individual icons
        # The gradient drawn should be that icon's portion of the overall gradient,
        # not the full window gradient shrunk to fit in the icon
        pat = cairo.LinearGradient (0.0, 0.0, w, 0.0)
        pat.add_color_stop_rgba (0.001, 0.0, 0.0, 0.0, 0.8)
        pat.add_color_stop_rgba (1, 0.2, 0.2, 0.2, 0.8)

        cr.rectangle(x-1, y-1, w+2, h+2)
        cr.set_source(pat)
        cr.fill()

    def _draw_divider_line(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, 1)
        cr.set_source_rgba(0.08, 0.08, 0.08, 0.8)
        cr.fill()
        cr.rectangle(event.area.x, event.area.y+1, event.area.width, 1)
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
        cr.fill()

    def _append_icons(self, icons, files, path):
        for fi in files:
            image_box = ImageEventBox(None)
            image_box.set_size_request(64, 64)
            image_box.set_images(self.get_images(path + fi))
            image_box.connect("enter-notify-event", self._display_plus, self._parent._add_remove_widget)
            image_box.connect("leave-notify-event", self._remove_plus, self._parent._add_remove_widget)
            image_box.connect("button-release-event", self._create_folder, path + fi)
            image_box.show()
            icons.append(image_box)
        
    def _fill_table(self):
        icons = []
        
        for name in self._ENDLESS_ICON_NAMES:
            files = self._get_folder_icons(self._ENDLESS_ICON_PATH, name, '_normal')
            self._append_icons(icons, files, self._ENDLESS_ICON_PATH)

        files = self._get_folder_icons(self._DEFAULT_ICON_PATH, 'folder')
        self._append_icons(icons, files, self._DEFAULT_ICON_PATH)

        num_of_icons = len(icons)
        available_width = screen_util.get_width(self._parent._parent.window) - self._parent._add_button_box_width - self._parent._tree_view_width
        columns = int(available_width/120)   # shold this be a fixed number like 5 as in pdf?
        rows = int(num_of_icons/columns) + 1
        self._table = gtk.Table(rows, columns)
        self._table.show()
        col = row = 0

        for num in range(len(icons)):
            if (num)%columns == 0:
                col = 0
                row = row + 1
            self._table.attach(icons[num], col, col+1, row, row+1, ypadding=25, xpadding=25)
            col = col + 1
