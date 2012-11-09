import gtk
from util.image_eventbox import ImageEventBox
from util import image_util
from util.transparent_window import TransparentWindow

class RemovalConfirmationPopupWindow():
    def __init__(self, callback, parent=None, widget=None, label=None, caller_widget=None):
        self._width = 91
        self._height = 91
        self._ok_active_images = (image_util.image_path("delete_ok_active.png"),)
        self._ok_inactive_images = (image_util.image_path("delete_ok_unactive.png"),)
        self._cancel_active_images = (image_util.image_path("delete_no_active.png"),)
        self._cancel_inactive_images = (image_util.image_path("delete_no_unactive.png"),)
        self._dialog_images = (image_util.image_path("delete_dialog_box.png"),)
        
        self._window = TransparentWindow(parent)
        self._window.set_size_request(self._width,self._height)
        self._window.set_position(gtk.WIN_POS_MOUSE)
        
        
        if caller_widget:
            self._move_window(caller_widget)
        
        self._window.connect("focus-out-event", lambda w, e: callback(False, widget, label))
        self._window.connect("focus-out-event", lambda w, e: self.destroy())
        
        self._fancy_container = ImageEventBox(self._dialog_images)
        self._fancy_container.set_size_request(self._width,self._height)
        self._bottom_center = gtk.Alignment(.5,.85,0,0)
        
        self._container = gtk.VBox(False)
        
        self._button_box = gtk.HBox(True)
        self._button_box.set_size_request(75,36)
        
        self._cancel_event_box = ImageEventBox(self._cancel_inactive_images)
        self._cancel_event_box.set_size_request(36, 36)
        self._cancel_event_box.connect("enter-notify-event", self._switch_images, self._cancel_active_images)
        self._cancel_event_box.connect("leave-notify-event", self._switch_images, self._cancel_inactive_images)
        self._cancel_event_box.connect("button-release-event", lambda w, e: callback(False, widget, label))
        self._cancel_event_box.connect("button-release-event", lambda w, e: self.destroy())
        
        self._ok_event_box = ImageEventBox(self._ok_inactive_images)
        self._ok_event_box.set_size_request(36,36)
        self._ok_event_box.connect("enter-notify-event", self._switch_images, self._ok_active_images)
        self._ok_event_box.connect("leave-notify-event", self._switch_images, self._ok_inactive_images)
        self._ok_event_box.connect("button-release-event", lambda w, e: callback(True, widget, label))
        self._ok_event_box.connect("button-release-event", lambda w, e: self.destroy())
        
        self._button_box.pack_start(self._cancel_event_box, True, True)
        self._button_box.pack_end(self._ok_event_box, True, True)
        
        self._bottom_center.add(self._button_box)
        
        self._fancy_container.add(self._bottom_center)
        self._window.add(self._fancy_container)
        self._window.show_all()
    
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
        
    def _switch_images(self, widget, event, images):
        widget.set_images(images)
        self._refresh_button(widget)
    
    def _refresh_button(self, widget):
        widget.hide()
        widget.show()
    
    def _move_window(self, caller_widget):
        new_x = caller_widget.allocation.x - int((self._width - caller_widget.allocation.width)/2)
        new_y = caller_widget.allocation.y + int((self._width - caller_widget.allocation.height)/2)
        self._window.move(new_x, new_y)
