import gtk

class NotificationPlugin(gtk.EventBox):
    SHADOW_OFFSET = 1

    def __init__(self, command):
        super(NotificationPlugin, self).__init__()
        self._command = command
        
    def get_launch_command(self):
        return self._command
