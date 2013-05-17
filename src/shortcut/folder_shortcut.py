from shortcut.desktop_shortcut import DesktopShortcut
from shortcut.application_shortcut import ApplicationShortcut
from eos_util import image_util
from eos_util.image import Image
from gi.repository import Gtk
from gi.repository import GObject

class FolderShortcut(DesktopShortcut):
    __gsignals__ = {
        "folder-shortcut-activate": (GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   GObject.TYPE_NONE,
                   (GObject.TYPE_STRING,GObject.TYPE_PYOBJECT)),
        "folder-shortcut-relocation": (GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   GObject.TYPE_NONE,
                   (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
    }


    def __init__(self, shortcut, callback, image=''):
        self._shortcut = shortcut
        self._normal_text = shortcut.name()

        super(FolderShortcut, self).__init__(shortcut.name())

        self._callback = callback

        self._icon_event_box.connect("button-release-event", self.mouse_release_callback)
        self._icon_event_box.connect("button-press-event", self.mouse_press_callback)
        self._icon_event_box.connect("enter-notify-event", self.mouse_over_callback)
        self._icon_event_box.connect("leave-notify-event", self.mouse_out_callback)

        self.show_all()
        self.set_moving(False)

        images = self.get_images(self.ICON_STATE_NORMAL)
        if len(images) > 0:
            self.set_dnd_icon(images[0])

    def _received_handler_callback(self, source, destination, x, y, data=None):
        source_widget = source.parent.parent

        if isinstance(source_widget, ApplicationShortcut):
            source_shortcut = source_widget.get_shortcut()
            if source_shortcut is not None:
                self.emit(
                    "folder-shortcut-relocation",
                    source_shortcut,
                    self.get_shortcut()
                    )

    def _drag_enter_handler_callback(self, source, destination):
        if isinstance(source.parent.parent, ApplicationShortcut):
            self.set_is_highlightable(True)
        else:
            self.set_is_highlightable(False)

    def _drag_leave_handler_callback(self, source, destination):
        self.set_is_highlightable(False)

    def mouse_release_callback(self, widget, event):
        if not self.is_moving():
            if event.button == 1:
                self.emit("folder-shortcut-activate", event, self._shortcut)
                self._icon_event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
                self._icon_event_box.hide()
                self._icon_event_box.show()
                return True
        return False

    def mouse_press_callback(self, widget, event):
        if event.button == 1:
            self._icon_event_box.set_images(self.get_images(self.ICON_STATE_PRESSED))
            self._icon_event_box.hide()
            self._icon_event_box.show()
            return True
        return False

    def mouse_out_callback(self, widget, event):
        self._icon_event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
        self._icon_event_box.hide()
        self._icon_event_box.show()
        return True

    def mouse_over_callback(self, widget, event):
        self._icon_event_box.set_images(self.get_images(self.ICON_STATE_MOUSEOVER))
        self._icon_event_box.hide()
        self._icon_event_box.show()
        return True

    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)

    def get_shortcut(self):
        return self._shortcut

    def get_images(self, event_state):
        shortcut_icon_dict = self._shortcut.icon()
        default_icon = shortcut_icon_dict.get(self.ICON_STATE_NORMAL, Image.from_name("folder.png"))
        return [Image.from_path(shortcut_icon_dict.get(event_state, default_icon))]

    def set_shortcut(self, shortcut):
        self._shortcut = shortcut
        self._identifier = shortcut.name()
        self._label_event_box._label.set_text(shortcut.name())
        self._label_event_box.refresh()
