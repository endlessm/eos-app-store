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
    
    # In the current design, all the notification windows
    # have the same width, and the height will grow as needed
    WINDOW_HEIGHT = -1
    
    # The window border leaves room for the triangle
    # that points up to the notification panel
    WINDOW_BORDER = 10

    def __init__(self, command):
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
