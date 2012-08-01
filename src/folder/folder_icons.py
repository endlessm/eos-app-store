import gtk
import gobject
from shortcut.application_shortcut import ApplicationShortcut

class FolderIcons(gtk.HBox):
    __gsignals__ = {
        "application-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self, shortcuts):
        gtk.HBox.__init__(self)
        
        for shortcut in shortcuts:
            app_shortcut = ApplicationShortcut(shortcut, False)
            self.pack_start(app_shortcut, False, False, 30) 
            app_shortcut.connect("application-shortcut-activate", lambda w, app_id, params: self.emit("application-shortcut-activate", app_id, params))