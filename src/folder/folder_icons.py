import gtk
import gobject
from shortcut.application_shortcut import ApplicationShortcut

class FolderIcons(gtk.HBox):
    __gsignals__ = {
        "application-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,)),
    }
    
    def __init__(self, shortcuts):
        gtk.HBox.__init__(self)
        
        
        for shortcut in shortcuts:
#            app_icon = shortcuts[shortcut]
            app_shortcut = ApplicationShortcut(shortcut)
            self.pack_start(app_shortcut, False, False, 30) 
            app_shortcut.connect("application-shortcut-activate", lambda w, app_id: self.emit("application-shortcut-activate", app_id))