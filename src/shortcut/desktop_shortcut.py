import string
from util import label_util
import gobject
from util.shadowed_label_box import ShadowedLabelBox
from eos_widgets.image_eventbox import ImageEventBox
from eos_util import image_util
import gtk

class DesktopShortcut(gtk.VBox):
    DND_TARGET_TYPE_TEXT = 80
    DND_TRANSFER_TYPE = [( "text/plain", gtk.TARGET_SAME_APP, DND_TARGET_TYPE_TEXT )]
    ICON_STATE_NORMAL = 'normal'
    ICON_STATE_PRESSED = 'pressed'
    ICON_STATE_MOUSEOVER = 'mouseover'

    __gsignals__ = {
        "desktop-shortcut-dnd-begin": (
            gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            gobject.TYPE_NONE,
            (),
            ),
        }

    _motion_callbacks = []
    _drag_end_callbacks = []
    _drag_begin_callbacks = []
    @classmethod
    def _add_motion_broadcast_callback(cls, callback):
        cls._motion_callbacks.append(callback)

    @classmethod
    def _add_drag_end_broadcast_callback(cls, callback):
        cls._drag_end_callbacks.append(callback)

    @classmethod
    def _add_drag_begin_broadcast_callback(cls, callback):
        cls._drag_begin_callbacks.append(callback)

    @classmethod
    def _motion_broadcast(cls, source, destination, x, y):
        for cb in cls._motion_callbacks:
            cb(source, destination, x, y)

    @classmethod
    def _drag_end_broadcast(cls, source):
        for cb in cls._drag_end_callbacks:
            cb(source)

    @classmethod
    def _drag_begin_broadcast(cls, source):
        for cb in cls._drag_begin_callbacks:
            cb(source)

    def __init__(self, label_text="", draggable=True, highlightable=True):
        super(DesktopShortcut, self).__init__()
        self.__dnd_enter_flag = False
        self.set_size_request(64, 64)
        self._event_box = self._create_icon(self.get_images(self.ICON_STATE_NORMAL))

        self._label = gtk.Label(label_text)
        self._identifier = label_text
        self._event_box._identifier = label_text

        new_style = self._label.get_style().copy()
        new_style.fg[gtk.STATE_NORMAL] = self._label.get_colormap().alloc('#f0f0f0')
        self._label.set_style(new_style)

        text = string.strip(label_text)
        self._label.set_text(label_util.wrap_text(self._label, text))

        self._label.set_alignment(0.5, 0.0)

        self._label_event_box = ShadowedLabelBox(self._label)

        self.pack_start(self._event_box, False, False, 3)
        self.pack_start(self._label_event_box, False, False, 3)

        self.highlightable = highlightable
        if draggable:
            self._event_box.connect("drag_data_get", self.dnd_send_data)
            self._event_box.drag_source_set(
                gtk.gdk.BUTTON1_MASK,
                self.DND_TRANSFER_TYPE,
                gtk.gdk.ACTION_MOVE
                )
        self._event_box.connect("drag_data_received", self.dnd_receive_data)
        self._event_box.connect("drag_motion", self.dnd_motion_data)
        self._event_box.connect("drag_end", self.dnd_drag_end)
        self._event_box.connect("drag_begin", self.dnd_drag_begin)
        self._event_box.connect("drag_leave", self.dnd_drag_leave)
        self._event_box.drag_dest_set(
            #gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_DROP,
            self.DND_TRANSFER_TYPE,
            gtk.gdk.ACTION_MOVE
            )
        
    def __str__(self):
        return self._event_box._identifier
        
    def set_is_highlightable(self, value):
        self.highlightable = value
        
    def set_dnd_icon(self, image):
        image = image_util.scrub_image_path(image)
        pixbuf = image_util.load_pixbuf(image)
        if (pixbuf.get_width() > 48) or (pixbuf.get_height() > 48):
            pixbuf = pixbuf.scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
        self._event_box.drag_source_set_icon_pixbuf(pixbuf)

    def dnd_send_data(self, widget, context, selection, targetType, eventTime):
        if targetType == self.DND_TARGET_TYPE_TEXT:
            if hasattr(self, '_transmiter_handler_callback'):
                data = self._transmiter_handler_callback(widget)
                selection.set(selection.target, 8, data)
            else:
                selection.set(selection.target, 8, self._identifier)

    def dnd_receive_data(self, widget, context, x, y, selection, targetType, time):
        source_widget = context.get_source_widget()
        if targetType == self.DND_TARGET_TYPE_TEXT:
            if hasattr(self, '_received_handler_callback'):
                self._received_handler_callback(
                    source_widget,
                    widget,
                    x,
                    y,
                    selection.data
                    )

    def dnd_motion_data(self, widget, context, x, y, time):
        if not self.__dnd_enter_flag:
            self.__dnd_enter_flag = True
            self.dnd_drag_enter(widget, context, time)
        source_widget = context.get_source_widget()
        DesktopShortcut._motion_broadcast(source_widget, widget, x, y)
        if hasattr(self, '_motion_handler_callback'):
            self._motion_handler_callback(source_widget, widget, x, y)
        context.drag_status(gtk.gdk.ACTION_MOVE, time)
        return True

    def dnd_drag_end(self, widget, context):
        self._label.show()
        self._event_box.show()
        self.set_moving(False)
        DesktopShortcut._drag_end_broadcast(widget)
        if hasattr(self, '_drag_end_handler_callback'):
            self._drag_end_handler_callback(widget)

    def dnd_drag_begin(self, widget, context):
        self._label.hide()
        self._event_box.hide()
        self.set_moving(True)
        DesktopShortcut._drag_begin_broadcast(widget)
        self.emit("desktop-shortcut-dnd-begin")
        if hasattr(self, '_drag_begin_handler_callback'):
            self._drag_begin_handler_callback(widget)

    def dnd_drag_leave(self, widget, context, time):
        self.__dnd_enter_flag = False
        source_widget = context.get_source_widget()
        if hasattr(self, '_drag_leave_handler_callback'):
            self._drag_leave_handler_callback(source_widget, widget)
        self._refresh()

    def dnd_drag_enter(self, widget, context, time):
        source_widget = context.get_source_widget()
        if hasattr(self, '_drag_enter_handler_callback'):
            self._drag_enter_handler_callback(source_widget, widget)
        if self.highlightable:
            self._refresh(self.get_highlight_images(self.ICON_STATE_MOUSEOVER))

    def set_moving(self, is_moving):
        self._is_moving = is_moving

    def is_moving(self):
        return self._is_moving

    def _refresh(self, images=None):
        images = images or self.get_images(self.ICON_STATE_NORMAL)
        self._event_box.set_images(images)
        #self._event_box.repaint()

    def get_shortcut(self):
        return None

    def get_images(self, event_state):
        return ()

    def get_highlight_images(self, event_state):
        return self.get_images(event_state)

    def remove_shortcut(self):
        if self.parent != None:
            self.parent.remove(self)

            for callback in self._callbacks:
                self.disconnect_by_func(callback)

            self._callbacks = []

    def connect(self, signal, callback, force=False):
        if not hasattr(self, "_callbacks"):
            self._callbacks = []

        if not hasattr(self, "_signals"):
            self._signals = {}

        if force or (not self._signals.has_key(signal)):
            self._signals[signal] = callback
            super(DesktopShortcut, self).connect(signal, callback)
            self._callbacks.append(callback)

    def _create_event_box(self):
        event_box = gtk.EventBox()
        event_box.set_size_request(64,64)
        event_box.set_visible_window(False)
        event_box.show()

        return event_box

    def _create_icon(self, images):
        icon = ImageEventBox(images)
        icon.set_size_request(64,64)
        icon.set_visible_window(False)
        icon.show()

        return icon
        
    def destroy(self):
        self.unparent()
        self._label.destroy()
        self._event_box.destroy()
        

