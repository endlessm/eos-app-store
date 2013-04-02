import gtk

from eos_util.image import Image
from settings_app_presenter import SettingsAppPresenter
from notification_plugin import NotificationPlugin
from taskbar_panel.taskbar_shortcut import TaskbarShortcut

class SettingsAppPlugin(NotificationPlugin, TaskbarShortcut):
    def __init__(self, icon_size):
        self._presenter = SettingsAppPresenter()
        if not self.is_launcher_present(self.get_path()):
            icon_size = 0
        
        NotificationPlugin.__init__(self, self._presenter.get_path())
        
        self._icon_size = icon_size

        self._pixbuf_normal = Image.from_name('settings_normal.png')
        self._pixbuf_hover = Image.from_name('settings_hover.png')
        self._pixbuf_down = Image.from_name('settings_down.png')

        self._settings_icon = gtk.Image()

        self._pixbuf_normal.draw(self._settings_icon.set_from_pixbuf)

        self.add(self._settings_icon)
        self.show_all()
        self.set_visible_window(False)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._settings_icon, self._pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._settings_icon, self._pixbuf_normal))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._settings_icon, self._pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._settings_icon, self._pixbuf_normal))

    def get_path(self):
        return self._presenter.get_path()

    def toggle_image(self, image, pixbuf):
        pixbuf.draw(image.set_from_pixbuf)

