import gtk

from osapps.app_launcher import AppLauncher
import gobject

class NotificationPlugin(gtk.EventBox):
    __gsignals__ = {
                    'hide-window-event': (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                                         gobject.TYPE_NONE,
                                         ()),
    }

    SHADOW_OFFSET = 1

    def __init__(self, command = None):
        super(NotificationPlugin, self).__init__()
        self._command = command

    def execute(self):
        AppLauncher().launch(self.get_launch_command())

    @staticmethod
    def is_plugin_enabled():
        # Default to enabled unless overridden by specific class
        return True


    def _hide_window(self, widget):
        pass
        
    def get_launch_command(self):
        return self._command

    def set_parent(self, parent):
        self._parent = parent
