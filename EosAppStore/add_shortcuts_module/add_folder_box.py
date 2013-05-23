from gi.repository import Gtk
import cairo
import gettext
import os

from EosAppStore.desktop.desktop_layout import DesktopLayout
from EosAppStore.eos_widgets.image_eventbox import ImageEventBox
from EosAppStore.eos_util.image import Image
from EosAppStore.eos_util import screen_util
from EosAppStore.osapps.desktop_preferences_datastore import DesktopPreferencesDatastore

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class AddFolderBox(Gtk.Box):
    BASEPATH = os.environ["XDG_DATA_DIRS"].split(":")[0] if os.environ["XDG_DATA_DIRS"] else "/usr/share"
    _FOLDER_ICON_PATH = BASEPATH + '/icons/EndlessOS/64x64/folders'

    def __init__(self, parent, add_remove_widget=None, desktop_preference_class = DesktopPreferencesDatastore):
        super(AddFolderBox, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_homogeneous(True)

        self._parent = parent


        self._desktop_preferences = desktop_preference_class.get_instance()
        # TODO should not rely on access to private member _parent of parent
        # Is there a better way to get access to the desktop window for its size?

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.connect("show", self._on_show)
        self._scrolled_window.get_vscrollbar().connect("value-changed", self._on_scroll)

        self._scrolling = False

        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._vbox.set_homogeneous(False)
        self._vbox.set_spacing(15)
        self._vbox.connect("draw", self._handle_event)

        label_1_text = _('1. NAME YOUR FOLDER')
        self._label_1 = Gtk.Label()
        label_2_text = _('2. PICK A SYMBOL')
        self._label_2 = Gtk.Label()
        self._label_1.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold" size="16000">' + label_1_text + '</span>')
        self._label_2.set_markup('<span color="#aaaaaa" font="Novecento wide" font_weight="bold" size="16000">' + label_2_text + '</span>')

        self._text_entry_align = Gtk.Alignment()
        self._text_entry_align.set(0.5, 0.5, 0, 0)
        self._hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._hbox.set_size_request(186, 24)
        self._text_entry = Gtk.Entry()
        self._text_entry.set_max_length(50)
        self._text_entry.set_alignment(0.5)
        self._hbox.pack_start(self._text_entry, True, True, 0)
        self._text_entry.set_text('')
        self._text_entry_align.add(self._hbox)

        self.hbox_separator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox_separator.set_size_request(-1, 15)
        self._vbox.pack_start(self.hbox_separator, True, True, 0)
        self._vbox.pack_start(self._label_1, True, True, 0)
        self._vbox.pack_start(self._text_entry_align, False, False, 0)
        self.hbox_separator1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox_separator1.set_size_request(-1, 15)
        #self.hbox_separator1.connect("draw", self._draw_divider_line)
        self._vbox.pack_start(self.hbox_separator1, False, False, 0)
        self._vbox.pack_start(self._label_2, True, True, 0)

        self._fill_table()

        self._table.show()
        self._bottom_center = Gtk.Alignment()
        self._bottom_center.set(0.5, 0, 0, 0)
        self._bottom_center.add(self._table)
        self._vbox.pack_start(self._bottom_center, False, False, 0)
        self._scrolled_window.add_with_viewport(self._vbox)
        self.add(self._scrolled_window)

        self.x = 0
        self.y = 0

        self.show_all()

    def _get_folder_icons(self, path='', prefix='', suffix=''):
        return self._parent._presenter.get_folder_icons(path, prefix, suffix)

    def get_images(self, image_path):
        return (
            Image.from_path(image_path),
            )

    def _display_plus(self, widget, event, add_remove_widget):
        images_tuple = widget._images
        images_list = list(images_tuple)
        images_list.append(Image.from_name("add_folder_icon.png"))
        widget.set_images(tuple(images_list))
        widget.hide()
        widget.show()
        add_remove_widget._icon_event_box.set_images(images_tuple)
        add_remove_widget._label.set_text(self._text_entry.get_text())
        add_remove_widget.hide()
        add_remove_widget.show()

    def _remove_plus(self, widget, event, add_remove_widget):
        images = list(widget._images)
        widget.set_images(tuple(images[:-1]))
        widget.hide()
        widget.show()
        add_remove_widget._icon_event_box.set_images(add_remove_widget.get_images('normal'))
        add_remove_widget._label.set_text('')
        add_remove_widget.hide()
        add_remove_widget.show()

    def _create_folder(self, widget, event, image_file):
        if self._text_entry.get_text() != 'Untitled' and self._text_entry.get_text():
            self._parent.create_folder(self._text_entry.get_text(), image_file)
            self._parent.destroy(None, None)
        else:
            print 'FOLDER MUST HAVE A NAME!'

    def _handle_event(self, widget, cr):
        x, y, _ = self._vbox.get_window().get_origin()
        top_x, top_y, _ = self._scrolled_window.get_window().get_toplevel().get_origin()
        self.draw(cr, x - top_x, y - top_y, self.get_allocation().width, self.get_allocation().height)

        # if event:
        #     self._draw_gradient(cr, event.area.width, event.area.height, event.area.x, event.area.y)

        return False

    def draw(self, cr, x, y, w, h):
        self._scrolled_window.get_child().set_shadow_type(Gtk.ShadowType.NONE)
        # Only copy/crop the background the first time through
        # to avoid needless memory copies and image manipulation
        if not self._scrolling:
            self._scrolling = True
        scroll_y = self._scrolled_window.get_vscrollbar().get_value()
        cr.paint()

    def _draw_gradient(self, cr, w, h, x=0, y=0):
        # TODO This is not quite appropriate when drawing the individual icons
        # The gradient drawn should be that icon's portion of the overall gradient,
        # not the full window gradient shrunk to fit in the icon
        pat = cairo.LinearGradient (0.0, 0.0, w, 0.0)
        pat.add_color_stop_rgba (0.001, 0.0, 0.0, 0.0, 0.8)
        pat.add_color_stop_rgba (1, 0.2, 0.2, 0.2, 0.8)

        cr.rectangle(x, y, w, h)
        cr.set_source(pat)
        cr.fill()

    def _draw_divider_line(self, widget, cr):
        cr.rectangle(event.area.x, event.area.y, event.area.width, 1)
        cr.set_source_rgba(0.08, 0.08, 0.08, 0.8)
        cr.fill()
        cr.rectangle(event.area.x, event.area.y+1, event.area.width, 1)
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
        cr.fill()

    def _append_icons(self, icons, files, path):
        for fi in files:
            image_file = os.path.join(path, fi)
            # ImageEventBox is currently broken,
            # so bypassing to use a Gtk.Image directly
            # image_box = ImageEventBox(None)
            image_box = Gtk.Image()
            image_box.set_size_request(DesktopLayout.ICON_WIDTH, DesktopLayout.ICON_HEIGHT)
            # image_box.set_images(self.get_images(image_file))
            image_box.set_from_file(image_file)

            image_box.connect("enter-notify-event", self._display_plus, self._parent._add_remove_widget)
            image_box.connect("leave-notify-event", self._remove_plus, self._parent._add_remove_widget)
            image_box.connect("button-release-event", self._create_folder, image_file)
            image_box.show()
            icons.append(image_box)
        
    def _fill_table(self):
        icons = []
        files = self._get_folder_icons(self._FOLDER_ICON_PATH, suffix='')
        self._append_icons(icons, files, self._FOLDER_ICON_PATH)
        num_of_icons = len(icons)
        available_width = screen_util.get_width(self._parent) - self._parent.add_button_box_width - self._parent.tree_view_width
        columns = int(available_width/120)   # shold this be a fixed number like 5 as in pdf?
        rows = int(num_of_icons/columns) + 1
        self._table = Gtk.Table(rows, columns)
        self._table.show()
        col = row = 0

        for num in range(len(icons)):
            if (num)%columns == 0:
                col = 0
                row = row + 1
            self._table.attach(icons[num], col, col+1, row, row+1, ypadding=25, xpadding=25)
            col = col + 1

    def _on_show(self, widget):
        widget.get_child().set_shadow_type(Gtk.ShadowType.NONE)
        
    def _on_scroll(self, widget):
        self._scrolled_window.queue_draw()
        
