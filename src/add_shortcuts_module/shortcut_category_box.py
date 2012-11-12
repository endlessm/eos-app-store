import gtk
import cairo
from eos_widgets.image_eventbox import ImageEventBox
from eos_util import image_util

class ShortcutCategoryBox(gtk.EventBox):
    def __init__(self, model, parent, width):
        super(ShortcutCategoryBox, self).__init__()
        self.set_visible_window(False)
        self._parent = parent
        self._width = width
        self._model = model
        self._separator_active = image_util.image_path('category_separator_active.png')
        self._separator_inactive = image_util.image_path('category_separator_inactive.png')
        
        self.top_align = gtk.Alignment(0.03, 0, 0, 0)
        self.middle_align = gtk.Alignment(0, 0.5, 0, 0)        
        
        self.tree = gtk.VBox()
        self.top = gtk.HBox()
        
        self._close = ImageEventBox((image_util.image_path("delete_no_unactive_24.png"),))
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        self.top.pack_start(self._close)
        self.top_align.add(self.top)
        self.top_align.show()
        
        self.middle = gtk.VBox()
        
        self._fill_categories()
        
        self.middle_align.add(self.middle)
        self.bottom = gtk.HBox()
        self.bottom.set_size_request(24, 24)

        self.tree.pack_start(self.top_align)
        self.tree.pack_start(self.middle_align)
        self.tree.pack_start(self.bottom)
        self.add(self.tree)
        self.connect("expose-event", self._draw_gradient)
        self.show_all()

    
    def _handle_click(self, widget, event, label):
        print label.get_text(), 'clicked, do something about it.'

    
    def _draw_gradient(self, widget, event, active=False):
        cr = widget.window.cairo_create()
        
        if not active:
            pat = cairo.LinearGradient (0.0, 0.0, widget.allocation.width, 0.0)
            cr.rectangle(widget.allocation.x, widget.allocation.y, widget.allocation.width, widget.allocation.height)
        else:
            pat = cairo.LinearGradient (0.0, 0.0, self._width, 0.0)
            cr.rectangle(widget.allocation.x, widget.allocation.y, self._width, widget.allocation.height)
        
        pat.add_color_stop_rgba (0.001, 0.0, 0.0, 0.0, 0.8)
        pat.add_color_stop_rgba (1, 0.2, 0.2, 0.2, 0.8)
        
        cr.set_source(pat)
        cr.fill()
    
    
    def destroy(self):
        self._parent.destroy()
    
    def _fill_categories(self):
        for section in self._model:
            image_start = gtk.Image()
            image_end = gtk.Image()
            box = gtk.EventBox()
            box.set_visible_window(False)
            
            if section.active:
                markup = '<span color="#ffffff"><b>' + section.category + '</b></span>'
                image_start.set_from_file(self._separator_active)
                image_end.set_from_file(self._separator_active)
                box.connect("expose-event", self._draw_gradient, True)
            else:
                markup = '<span color="#aaaaaa"><b>' + section.category + '</b></span>'
                image_start.set_from_file(self._separator_inactive)
                image_end.set_from_file(self._separator_inactive)
            
            vbox = gtk.VBox(False)
            hbox = gtk.HBox()
            label = gtk.Label()
            label.set_markup(markup)
            label.set_alignment(0, 0.5)
            hbox.pack_start(label, True, True, 20)
            vbox.pack_start(image_start)
            vbox.pack_start(hbox, True, True, 15)
            vbox.pack_end(image_end)
            box.add(vbox)
            box.connect("button-release-event", self._handle_click, label)
            self.middle.pack_start(box)
