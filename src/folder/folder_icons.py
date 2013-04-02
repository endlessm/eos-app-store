import gtk
import gobject
from shortcut.application_shortcut import ApplicationShortcut

class FolderIcons(gtk.HBox):
    __gsignals__ = {
        "application-shortcut-activate": (
            gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, )
            ), 
        "desktop-shortcut-dnd-begin": (
            gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            gobject.TYPE_NONE,
            ()
            ),
         "desktop-shortcut-rename": (
            gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT),
            ),
    }
    
    def __init__(self, shortcuts, spacing=0):
        gtk.HBox.__init__(self)
        super(FolderIcons, self).__init__(homogeneous=False, spacing=spacing)
        
        for shortcut in shortcuts:
            app_shortcut = ApplicationShortcut(shortcut, False)
            self.pack_start(app_shortcut, False, False, padding=0)
            app_shortcut.connect(
                "application-shortcut-activate", 
                lambda w, app_id, params: self.emit(
                    "application-shortcut-activate", 
                    app_id, 
                    params
                    )
                )
            app_shortcut.connect(
                "desktop-shortcut-dnd-begin", 
                lambda w: self.emit(
                    "desktop-shortcut-dnd-begin"
                    )
                )
            app_shortcut.connect(
                "desktop-shortcut-rename", 
                lambda w, new_name: self.emit("desktop-shortcut-rename", new_name, w)
                )