from gi.repository import Gtk
import cairo
from EosAppStore.eos_widgets.image_eventbox import ImageEventBox
from EosAppStore.eos_util.image import Image

class ShortcutCategoryBox(Gtk.EventBox):
    def __init__(self, model, parent, width, presenter):
        super(ShortcutCategoryBox, self).__init__()
        self.set_visible_window(False)
        self._parent = parent
        self._presenter = presenter
        self._width = width
        self._model = model
        self._active_category = None
        self._active_subcategory = None
        self._separator_active = Image.from_name('category_separator_active.png')
        self._separator_inactive = Image.from_name('category_separator_inactive.png')
        self.top_align = Gtk.Alignment()
        self.top_align.set(0.03, 0, 0, 0)
        self.middle_align = Gtk.Alignment()
        self.middle_align.set(0, 0.5, 0, 0)

        self.tree = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self._close = ImageEventBox((Image.from_name("delete_no_unactive_24.png"),))
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        self.top.pack_start(self._close, True, True, 0)
        self.top_align.add(self.top)
        self.top_align.show()

        self.middle = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self._fill_categories()

        self.middle_align.add(self.middle)
        self.bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.bottom.set_size_request(24, 24)

        self.tree.pack_start(self.top_align, True, True, 0)
        self.tree.pack_start(self.middle_align, True, True, 0)
        self.tree.pack_start(self.bottom, True, True, 0)
        self.add(self.tree)
        self.connect("draw", self._draw_gradient)
        self.show_all()

    def _handle_click(self, widget, event, label, subcategory=''):
        #change model and repaint categories box
        for section in self._model:
            if section.category == label.get_text():
                section.active = True
            else:
                section.active = False
        self.refresh_categories()
        self._presenter.set_add_shortcuts_box(label.get_text(), subcategory)

    def _draw_gradient(self, widget, cr, active=False):
        if not active:
            pat = cairo.LinearGradient (0.0, 0.0, widget.get_allocation().width, 0.0)
            cr.rectangle(widget.get_allocation().x, widget.get_allocation().y, widget.get_allocation().width, widget.get_allocation().height)
        else:
            pat = cairo.LinearGradient (0.0, 0.0, self._width, 0.0)
            cr.rectangle(widget.get_allocation().x, widget.get_allocation().y, self._width, widget.get_allocation().height)

        pat.add_color_stop_rgba (0.001, 0.0, 0.0, 0.0, 0.8)
        pat.add_color_stop_rgba (1, 0.2, 0.2, 0.2, 0.8)

        cr.set_source(pat)
        cr.fill()

    def destroy(self):
        self._parent.destroy()

    def _fill_categories(self):
        for section in self._model:
            image_start = Gtk.Image()
            image_end = Gtk.Image()
            box = Gtk.EventBox()
            box.set_visible_window(False)
            markup = self._set_markup_and_separators(section, image_start, image_end, box)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.set_homogeneous(False)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label()
            label.set_markup(markup)
            label.set_alignment(0, 0.5)
            label.uat_id = section.category.lower() + "_tab"
            hbox.pack_start(label, True, True, 20)
            vbox.pack_start(image_start, True, True, 0)
            vbox.pack_start(hbox, True, True, 15)
            if section.subcategories:
                for category in section.subcategories:
                    if category.active:
                        self._active_subcategory = category.category
            
            # For now, we only support a single subcategory,
            # so hide the display of the word "ALL"
            # Re-enable the lines below once subcategory support
            # is added back into the design.
            # if section.subcategories and section.active:
            #     self._fill_subcategories(section, vbox)
            
            vbox.pack_end(image_end, True, True, 0)
            box.add(vbox)
            box.connect("button-release-event", self._handle_click, label, self._active_subcategory)
            box.show()
            self.middle.pack_start(box, True, True, 0)

    def _handle_subcategory_click(self, widget, event, category, subcategory):
        for section in self._model:
            if section.category == category:
                section.active = True
            else:
                section.active = False
            if section.subcategories:
                for subcat in section.subcategories:
                    if subcat.category == subcategory:
                        subcat.active = True
                    else:
                        subcat.active = False
        self.refresh_categories()
        self._presenter.set_add_shortcuts_box(category, subcategory)
    
    def refresh_categories(self):
        for child in self.middle.get_children():
            self.middle.remove(child)
            child.destroy()
        self._fill_categories()
        self.middle.show_all()
    
    def _fill_subcategories(self, section, vbox):
        for category in section.subcategories:
            subcategories_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            subcategory_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            ebox = Gtk.EventBox()
            ebox.set_visible_window(False)
            sub_label = Gtk.Label()
            if category.active:
                sub_label.set_markup('<span color="#ffffff"><b>' + category.category.upper() + '</b></span>')
            else:
                sub_label.set_markup('<span color="#aaaaaa"><b>' + category.category.upper() + '</b></span>')
            sub_label.set_alignment(0, 0.5)
            ebox.add(sub_label)
            ebox.connect("button-release-event", self._handle_subcategory_click, section.category, category.category)
            subcategory_hbox.pack_start(ebox, True, True, 20)
            subcategories_vbox.pack_start(subcategory_hbox, True, True, 5)
            vbox.pack_start(subcategories_vbox, True, True, 0)
    
    def _set_markup_and_separators(self, section, image_start, image_end, box):
        if section.active:
            markup = '<span color="#ffffff"><b>' + section.category.upper() + '</b></span>'
            self._active_category = section.category
            image_start.set_from_pixbuf(self._separator_active.pixbuf)
            image_end.set_from_pixbuf(self._separator_active.pixbuf)
            box.connect("draw", self._draw_gradient, True)
        else:
            markup = '<span color="#aaaaaa"><b>' + section.category.upper() + '</b></span>'
            image_start.set_from_pixbuf(self._separator_inactive.pixbuf)
            image_end.set_from_pixbuf(self._separator_inactive.pixbuf)
        
        return markup
    
