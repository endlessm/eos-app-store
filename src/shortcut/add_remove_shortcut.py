import gobject
from shortcut.desktop_shortcut import DesktopShortcut
from removal_module.removal_confirmation_popup_window import RemovalConfirmationPopupWindow
from removal_module.delete_not_possible_popup import DeleteNotPossiblePopupWindow
from eos_util.image import Image

class AddRemoveShortcut(DesktopShortcut):
    __gsignals__ = {
        "application-shortcut-remove": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
           gobject.TYPE_NONE,
           (gobject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self, label_text="", callback=None):
        super(AddRemoveShortcut, self).__init__(label_text, draggable=False)
        
        #listen for drag begin on all widgets
        DesktopShortcut._add_drag_begin_broadcast_callback(
            self._drag_begin_broadcast_callback
            )
        #listen for drag end on all widgets
        DesktopShortcut._add_drag_end_broadcast_callback(
            self._drag_end_broadcast_callback
            )
        #Listen for motion on all widgets
        DesktopShortcut._add_motion_broadcast_callback(
            self._drag_motion_broadcast_callback
            )
        
        
        self._callback = callback
        
        self._normal_text = label_text
        
        self._icon_event_box.connect("drag_motion", lambda w, ctx, x, y, t: self._dragged_over())
        self._icon_event_box.connect("button-press-event", self.mouse_press_callback)
        self._icon_event_box.connect("drag_leave", self.dnd_drag_leave)
        
        self._plus_images = ()
        self._empty_trash_images = ()
        self._full_trash_images = ()
        self._drag_data = {}

        self.show_all()
        
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
            
    def get_images(self, event_state):
        return [
            Image.from_name("endless-shortcut-well.png"),
            Image.from_name("endless-add.png"),
            Image.from_name("endless-shortcut-foreground.png")
            ]
    
    def get_dragged_images(self):
        return (
            Image.from_name("endless-shortcut-well.png"),
            Image.from_name("trash_empty_icon.png"),
            Image.from_name("endless-shortcut-foreground.png")
            )

    def get_trash_full_images(self):
        return (
            Image.from_name("endless-shortcut-well.png"),
            Image.from_name("trash_full_icon.png"),
            Image.from_name("endless-shortcut-foreground.png")
            )
    
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
        pass
    
    def change_icon(self, images):
        self._icon_event_box.set_images(images)
        self._icon_event_box.hide()
        self._icon_event_box.show()
        
    def _drag_begin_broadcast_callback(self, widget):
        if widget._identifier != _('Files'):
            self.change_icon(self.get_dragged_images())
        
    def _drag_end_broadcast_callback(self, widget):
        self.change_icon(self.get_images(self.ICON_STATE_NORMAL))
    
    def dnd_drag_leave(self, widget, context, time):
        source_widget = context.get_source_widget()
        if source_widget._identifier != _('Files'):
            self.change_icon(self.get_dragged_images())

        
    def dnd_receive_data(self, widget, context, x, y, selection, targetType, time):
        source_widget = context.get_source_widget().parent
        label = source_widget.parent._label.get_text()
        
        if label == _('Files'):
            return
        
        super(AddRemoveShortcut, self).dnd_motion_data(widget, context, x, y, time)
        if len(source_widget.parent._shortcut.children()) == 0:
            self._confirmation_popup = RemovalConfirmationPopupWindow(self._confirmation_received, parent=self.get_toplevel(), caller_widget=self._icon_event_box, widget=source_widget, label=label)
            self._confirmation_popup.show()
            source_widget.parent._icon_event_box.set_images(())
            source_widget.parent._label.set_text('')
            source_widget.parent._label_event_box._label.set_text('')
            source_widget.parent._label_event_box.refresh()
        else:
            self._delete_not_possible_popup = DeleteNotPossiblePopupWindow(parent=self.get_toplevel())
            self._delete_not_possible_popup.show()

    def _drag_motion_broadcast_callback(self, source, destination, x, y):
        if isinstance(destination.parent.parent, AddRemoveShortcut) and source._identifier != _('Files'):
            self.change_icon(self.get_trash_full_images())
    
    def _confirmation_received(self, result, widget, lbl):
        if result:
            self.emit("application-shortcut-remove", widget.parent.get_shortcut())
        else:
            widget.parent.set_images(widget.parent.get_images(self.ICON_STATE_NORMAL))
            widget.hide()
            widget.show()
            widget.parent._label.set_text(lbl)
            widget.parent._label_event_box._label.set_text(lbl)
            widget.parent._label_event_box.refresh()
            widget.parent._label.hide()
            widget.parent._label.show()

        self.change_icon(self.get_images(self.ICON_STATE_NORMAL))
