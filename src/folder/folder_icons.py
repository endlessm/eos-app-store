from gi.repository import Gtk
from gi.repository import GObject
from shortcut.application_shortcut import ApplicationShortcut

class FolderIcons(Gtk.HBox):
    __gsignals__ = {
        "application-shortcut-activate": (
            GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            GObject.TYPE_NONE,
            (GObject.TYPE_STRING, GObject.TYPE_PYOBJECT, )
            ), 
        "desktop-shortcut-dnd-begin": (
            GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            GObject.TYPE_NONE,
            ()
            ),
         "desktop-shortcut-rename": (
            GObject.SIGNAL_RUN_FIRST, #@UndefinedVariable
            GObject.TYPE_NONE,
            (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT),
            ),
    }
    
    def __init__(self, shortcuts, spacing=0):
        Gtk.HBox.__init__(self)
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
