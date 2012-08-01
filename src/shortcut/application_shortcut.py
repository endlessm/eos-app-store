import gobject
import string
import gtk.keysyms
import gtk
from util import label_util, image_util
from shortcut.desktop_shortcut import DesktopShortcut

class ApplicationShortcut(DesktopShortcut):
    __gsignals__ = {
    "application-shortcut-rename": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING,)),
    "application-shortcut-move": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       ()),
    "application-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_STRING,)),
    "application-shortcut-drag": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_BOOLEAN,)),    
    }
    
    def __init__(self, shortcut, show_background=True):
        image_name = shortcut.icon() 
#        label_text = shortcut.display_name()
        label_text = shortcut.name()
        self._image_name = image_name
        self._show_background = show_background
        
        super(ApplicationShortcut, self).__init__(label_text)
        self._shortcut = shortcut
        
        self._event_box.connect("button-press-event", self.mouse_press_callback)
        self._event_box.connect("button-release-event", self.mouse_release_callback)
        
        self._event_box.set_data('id', self._shortcut.key())
        self._event_box.set_data('params', self._shortcut.params())
        
#        self._event_box.connect("drag_begin", lambda c, d: self._drag_begin())
#        self._event_box.connect("drag_end", lambda c, d: self._drag_end())
#        self._event_box.connect("drag_data_get", self._send_callback)
#        self._event_box.connect("drag_motion", lambda w, ctx, x, y, t: self._dragged_over(ctx.get_source_widget().get_data('id')))
#        self._event_box.connect("drag_data_received", self.drag_data_received_callback)
#        self._event_box.connect("drag-failed", lambda w, c, r: self.show_drag_failed_animation(w, c, r, True))

#        self._event_box.drag_source_set(gtk.gdk.BUTTON_PRESS_MASK, self.DND_TRANSFER_TYPE, gtk.gdk.ACTION_MOVE)
        
        self.show_all()
        self.set_moving(False)
        
#        self.add_rename_entry(label_text)

    def drag_data_received_callback(self, widget, context, x, y, selection, targetType, time):
        if targetType == self.DND_TARGET_TYPE_TEXT:
            self.emit("application-shortcut-move")
            
    def show_drag_failed_animation(self, widget, context, result, kill_animation):
        return kill_animation
       
    def get_images(self):
        if self._show_background:
            return (image_util.image_path("endless-shortcut-well.png"), image_util.image_path("endless-shortcut-background.png"), self._image_name, image_util.image_path("endless-shortcut-foreground.png"))
        else:
            return (image_util.image_path("endless-shortcut-well.png"), self._image_name,)

    def get_depressed_images(self):
        if self._show_background:
            return (image_util.image_path("endless-shortcut-well.png"),self._image_name,image_util.image_path("endless-shortcut-foreground.png"))
        else:
            return (image_util.image_path("endless-shortcut-well.png"), self._image_name, image_util.image_path("endless-shortcut-foreground.png"))
         
    def get_shortcut(self):
        return self._shortcut
        
    def _dragged_over(self, app_id):
        self.emit("application-shortcut-dragging-over", self._shortcut)
        
    def _drag_begin(self):
        self._label.hide()
        self._event_box.child.hide()
        self.set_moving(True)
        self.emit("application-shortcut-drag", True)
    
    def _drag_end(self):
        self._label.show()
        self._event_box.child.show()
        self.set_moving(False)
        self.emit("application-shortcut-drag", False)
        self.emit("application-shortcut-move")
        
    def _send_callback(self, widget, context, selection, targetType, eventTime):
        if targetType == self.DND_TARGET_TYPE_TEXT:
            selection.set(selection.target, 8, str(self._event_box.get_data('id')))
        
    def add_rename_entry(self, text):
        self.text_view = gtk.TextView()
        self.text_buffer = self.text_view.get_buffer()
        self.text_view.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.text_view.set_justification(gtk.JUSTIFY_CENTER)
        self.text_view.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('#000000'))
        self.text_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#cccccc')) 
        self.text_view.set_left_margin(5)
        self.text_view.set_right_margin(5)
        self.text_view.hide()

        if text != None:
            text = string.strip(text)
        else:
            text = ""
        self.text_buffer.set_text(string.strip(text))
        
        self.text_view.connect("focus-in-event", self.set_rename_flag)
        self.text_view.connect("focus-out-event", self.lost_focus)
        self.text_view.connect("key-press-event", self.handle_keystrokes)
        
        self.pack_start(self.text_view, False, False)
        
    def rename_icon(self, widget, event):
        self._label.hide()
        self.original_entry_text = self.text_buffer.get_text(self.text_buffer.get_start_iter(), self.text_buffer.get_end_iter(), False)
        self.text_view.grab_focus()
        self.text_view.emit("select-all", widget)
        self.text_view.show()
        
    def lost_focus(self, widget, event):
        if not self.rename_flag:
            self.rename_label(widget)
            self.text_view.get_buffer().set_text(self._label.get_text())
        
    def set_rename_flag(self, widget, event):
        self.rename_flag = False

    def rename_label(self, widget):
        self.rename_flag = True
        b = widget.get_buffer()
        text = string.strip(b.get_text(b.get_start_iter(), b.get_end_iter(), False))
        if (len(string.replace(text, " ", "")) <= 0):
            widget.get_buffer().set_text(self.original_entry_text)
            widget.hide()
            self._label.show()
            return
        
        self._label.set_text(label_util.wrap_text(self._label, text))
        self.emit("application-shortcut-rename", self._shortcut, text)
        widget.hide()
        self._label.show()
    
    def remove_shortcut(self):
        self.rename_flag = False
#        self.text_view.hide()
        super(ApplicationShortcut, self).remove_shortcut()
        
    def handle_keystrokes(self, widget, event):
        if(event.keyval == gtk.keysyms.Escape):
            self.rename_flag = True
            self.text_buffer.set_text(self.original_entry_text)
            self.text_view.hide()
            self._label.show()
            return True
        elif(event.keyval == gtk.keysyms.Return):
            self.rename_label(widget)
            return True
        return False
    
    def mouse_release_callback(self, widget, event):
        if event.button == 1:
            self._event_box.set_images(self.get_images())
            self._event_box.hide()
            self._event_box.show()
            return True
        
        return False
    
    def mouse_press_callback(self, widget, event):
        if event.button == 1: # and event.type == gtk.gdk._2BUTTON_PRESS:
            self.emit("application-shortcut-activate", self._shortcut.key())
            self._event_box.set_images(self.get_depressed_images())
            self._event_box.hide()
            self._event_box.show()
            return True
        return False