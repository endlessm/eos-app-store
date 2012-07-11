import gobject
from shortcut.desktop_shortcut import DesktopShortcut
from util import image_util

class AddRemoveShortcut(DesktopShortcut):
    __gsignals__ = {
        "application-shortcut-remove": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
           gobject.TYPE_NONE,
           (gobject.TYPE_STRING,)),
    }
    
    def __init__(self, label_text, callback):
        super(AddRemoveShortcut, self).__init__(label_text)
        
        self._callback = callback
        
        self._normal_text = label_text
        
        self._event_box.connect("drag_motion", lambda w, ctx, x, y, t: self._dragged_over())
        self._event_box.connect("button-press-event", self.mouse_press_callback)
        self._event_box.connect("drag_data_received", self.drag_data_received_callback)

        self.show_all()
        
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
            
    def get_images(self):
        return (image_util.image_path("endless-shortcut-well.png"),image_util.image_path("endless-add.png"),image_util.image_path("endless-shortcut-foreground.png"))
    
    def get_dragged_images(self):
#        return (image_util.image_path("endless-shortcut-well.png"),image_util.image_path("endless-trash.png"),image_util.image_path("endless-shortcut-foreground.png"))
        return (image_util.image_path("endless-trash.png"),)
        
    def drag_data_received_callback(self, widget, context, x, y, selection, targetType, time):
        if targetType == self.DND_TARGET_TYPE_TEXT:
            self.emit("application-shortcut-remove", selection.data)
    
    def mouse_press_callback(self, widget, event):
        if event.button == 1:
            self._callback(widget, event)
            return True
      
        return False

    def toggle_drag(self, is_dragging):
        if is_dragging:
            self._icon.set_images(self.get_dragged_images())
            self._label.set_text(_("Delete"))
            self._icon.show()
            return

        self._label.set_text(self._normal_text)
        self._icon.set_images(self.get_images())    
    
    def _dragged_over(self):
        self.emit("application-shortcut-dragging-over", None)