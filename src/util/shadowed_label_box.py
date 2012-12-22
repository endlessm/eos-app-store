import gtk
import cairo

from util.rename_widget import RenameWidget

class ShadowedLabelBox(gtk.EventBox):
    def __init__(self, label):
        super(ShadowedLabelBox, self).__init__()
        self.connect("expose-event", self.draw)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        if label.get_text():
            self.connect("button-press-event", self._click_handler)
        self._label = label
        self.SHADOW_OFFSET = 2
        self.SHADOW_ALPHA = 0.3
        
        self._text_layout = self.create_pango_layout(self._label.get_text())
        self._shadow_layout = self.create_pango_layout(self._label.get_text())
        
        self.add(self._label)
        
        self.set_visible_window(False)
    
    def draw(self, widget, event):
        text_size_x, text_size_y = self._text_layout.get_pixel_size()
        left_margin = int((self.allocation.width - text_size_x)/2)
        cr = widget.window.cairo_create()
        cr.save()
        cr.rectangle(self._label.allocation.x, self._label.allocation.y,
                     self._label.allocation.width, self._label.allocation.height)
        cr.clip()
        
        cr.set_source_rgba(0.0, 0.0, 0.0, self.SHADOW_ALPHA);
        cr.move_to(self._label.allocation.x + self.SHADOW_OFFSET + left_margin,
                   self._label.allocation.y + self.SHADOW_OFFSET)
        
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        cr.show_layout(self._shadow_layout)
        
        cr.restore()
    
    def _click_handler(self, widget, event):
        if event.button == 1:
            # Label box needs the same x offset as the icon
            xoffset = (112-64)/2
            yoffset = widget.get_toplevel().window.get_origin()[1]
            RenameWidget(x=self._label.allocation.x, y=self._label.allocation.y, caller=widget.parent, x_offset=xoffset, y_offset=yoffset)
        return False
    
    def refresh(self):
        self._text_layout = self.create_pango_layout(self._label.get_text())
        self._shadow_layout = self.create_pango_layout(self._label.get_text())
        self.draw(self, None)
