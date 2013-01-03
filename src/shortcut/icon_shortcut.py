import string
from util import label_util
import gobject
from util.shadowed_label_box import ShadowedLabelBox
from eos_widgets.image_eventbox import ImageEventBox
from desktop.desktop_layout import DesktopLayout
from desktop_shortcut import DesktopShortcut
from separator_shortcut import SeparatorShortcut
import gtk

class IconShortcut(DesktopShortcut):
    def __init__(self, label_text="", draggable=True, highlightable=True, has_icon=True,
                 width=DesktopLayout.LABEL_WIDTH_IN_PIXELS, height=DesktopLayout.ICON_HEIGHT):
#        super(DesktopShortcut, self).__init__()
        gtk.VBox.__init__(self)
        self.__dnd_enter_flag = False
        
        self._width = width
        self._height = height
#        self.set_size_request(width, height)
        
        if has_icon:
            # Use the standard icon dimensions
            # We will use a spacer to fill out the full dimensions
            # so that the label can extend into the space between icons
            self._icon_width = DesktopLayout.ICON_WIDTH
            self._icon_height = DesktopLayout.ICON_HEIGHT
        else:
            # Let the icon fill the entire shortcut dimensions
            self._icon_width = self._width
            self._icon_height = self._height
        
        self._icon_event_box = self._create_icon(self.get_images(self.ICON_STATE_NORMAL))
        
        self._centered_icon_hbox = gtk.HBox()
#        self._centered_icon_hbox.set_size_request(width, height)

        self.set_size_request(width, height)
        
        if has_icon:
            # Add spacers to center the icon within the shortcut
#            self._left_spacer = SeparatorShortcut(DesktopLayout.get_spacer_width(), height)
#            self._right_spacer = SeparatorShortcut(DesktopLayout.get_spacer_width(), height)
            self._left_spacer = gtk.VBox()
            self._left_spacer.set_size_request(DesktopLayout.get_spacer_width(), height)
            self._right_spacer = gtk.VBox()
            self._right_spacer.set_size_request(DesktopLayout.get_spacer_width(), height)
            self._centered_icon_hbox.pack_start(self._left_spacer, False, False)
            self._centered_icon_hbox.pack_start(self._icon_event_box, False, False)
            self._centered_icon_hbox.pack_start(self._right_spacer, False, False)
        else:
            self._centered_icon_hbox.pack_start(self._icon_event_box, False, False)
            
        self._label = gtk.Label(label_text)
        self._identifier = label_text
        self._centered_icon_hbox._identifier = label_text
        self._icon_event_box._identifier = label_text

        new_style = self._label.get_style().copy()
        new_style.fg[gtk.STATE_NORMAL] = self._label.get_colormap().alloc('#f0f0f0')
        self._label.set_style(new_style)

        text = string.strip(label_text)
        self._label.set_text(label_util.wrap_text(self._label, text))

        self._label.set_alignment(0.5, 0.0)

        self._label_event_box = ShadowedLabelBox(self._label)

        self.pack_start(self._centered_icon_hbox, False, False, 3)
        self.pack_start(self._label_event_box, False, False, 3)

        self.highlightable = highlightable
        if draggable:
            self._icon_event_box.connect("drag_data_get", self.dnd_send_data)
            self._icon_event_box.drag_source_set(
                gtk.gdk.BUTTON1_MASK,
                self.DND_TRANSFER_TYPE,
                gtk.gdk.ACTION_MOVE
                )
        self._icon_event_box.connect("drag_data_received", self.dnd_receive_data)
        self._icon_event_box.connect("drag_motion", self.dnd_motion_data)
        self._icon_event_box.connect("drag_end", self.dnd_drag_end)
        self._icon_event_box.connect("drag_begin", self.dnd_drag_begin)
        self._icon_event_box.connect("drag_leave", self.dnd_drag_leave)
        self._icon_event_box.drag_dest_set(
            #gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_DROP,
            self.DND_TRANSFER_TYPE,
            gtk.gdk.ACTION_MOVE
            )
