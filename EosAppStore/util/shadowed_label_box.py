from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import PangoCairo
import cairo

from EosAppStore.util.rename_widget import RenameWidget
from EosAppStore.desktop.desktop_layout import DesktopLayout

class ShadowedLabelBox(Gtk.EventBox):
    def __init__(self, label):
        super(ShadowedLabelBox, self).__init__()
        self.connect("draw", self.draw)
        self.add_events(Gdk.EventType.BUTTON_PRESS)
        if label.get_text():
            self.connect("button-press-event", self._click_handler)
        self._label = label
        self.SHADOW_OFFSET = 2
        self.SHADOW_ALPHA = 0.3
        
        self._text_layout = self.create_pango_layout(self._label.get_text())
        self._shadow_layout = self.create_pango_layout(self._label.get_text())
        
        self.add(self._label)
        
        self.set_visible_window(False)
    
    def draw(self, widget, cr):
        text_size_x, text_size_y = self._text_layout.get_pixel_size()
        left_margin = int((self.get_allocation().width - text_size_x)/2)
        cr.save()
        cr.rectangle(self._label.get_allocation().x, self._label.get_allocation().y,
                     self._label.get_allocation().width, self._label.get_allocation().height)
        cr.clip()
        
        cr.set_source_rgba(0.0, 0.0, 0.0, self.SHADOW_ALPHA);
        cr.move_to(self._label.get_allocation().x + self.SHADOW_OFFSET + left_margin,
                   self._label.get_allocation().y + self.SHADOW_OFFSET)
        
        cr.set_operator(cairo.OPERATOR_DEST_OUT);
        PangoCairo.show_layout(cr, self._shadow_layout)
        
        cr.restore()
    
    def _click_handler(self, widget, event):
        if event.button == 1:
            x_offset = 0
            y_offset = widget.get_toplevel().get_window().get_origin()[1]

            # If we don't keep a reference to the rename widget, its instance variables get removed
            # and callbacks break. This way, code works as expected and RenameWidget handles its own lifecycle
            self._reference = RenameWidget(x=self._label.get_allocation().x + x_offset, y=self._label.get_allocation().y + y_offset,
                         caller=widget.parent, caller_width=DesktopLayout.LABEL_WIDTH_IN_PIXELS)
        return False
    
    def refresh(self):
        self._text_layout = self.create_pango_layout(self._label.get_text())
        self._shadow_layout = self.create_pango_layout(self._label.get_text())
        self.draw(self, None)
