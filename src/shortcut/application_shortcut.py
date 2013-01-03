import gobject
import string
import gtk.keysyms
import gtk
from eos_util.image import Image
from util import label_util
from shortcut.desktop_shortcut import DesktopShortcut

class ApplicationShortcut(DesktopShortcut):
    __gsignals__ = {
    "application-shortcut-rename": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING,)),
    "application-shortcut-activate": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_STRING,gobject.TYPE_PYOBJECT,)),
    "application-shortcut-drag": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                       gobject.TYPE_NONE,
                       (gobject.TYPE_BOOLEAN,)),    
    }
    
    def __init__(self, shortcut, show_background=True):
        self._shortcut = shortcut
        label_text = shortcut.name()
        self._show_background = show_background
        
        super(ApplicationShortcut, self).__init__(label_text, highlightable=False)
        
        self._icon_event_box.connect("button-press-event", self.mouse_press_callback)
        self._icon_event_box.connect("button-release-event", self.mouse_release_callback)
        self._icon_event_box.connect("enter-notify-event", self.mouse_over_callback)
        self._icon_event_box.connect("leave-notify-event", self.mouse_out_callback)
        
        self._icon_event_box.set_data('id', self._shortcut.key())
        self._icon_event_box.set_data('params', self._shortcut.params())
        
        self.show_all()
        self.set_moving(False)
        
        images = self.get_images(self.ICON_STATE_NORMAL)
        if len(images) > 0:
            try:
                self.set_dnd_icon(images[0])
            except:
                # TODO should display a default icon
                # For now, at least catch the exception so that the desktop will load!
                pass
        
#        self.add_rename_entry(label_text)
       
    def get_images(self, event_state):
        shortcut_icon_dict = self._shortcut.icon()
        default_icon = shortcut_icon_dict.get(self.ICON_STATE_NORMAL)        
        return [Image.from_path(shortcut_icon_dict.get(event_state, default_icon))]
         
    def get_shortcut(self):
        return self._shortcut
        
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
        if not self.is_moving():
            if event.button == 1:
                self.emit("application-shortcut-activate", self._shortcut.key(), self._shortcut.params())
                self._icon_event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
                self._icon_event_box.hide()
                self._icon_event_box.show()
                return True
        return False
    
    def mouse_press_callback(self, widget, event):
        if event.button == 1: # and event.type == gtk.gdk._2BUTTON_PRESS:
            self._icon_event_box.set_images(self.get_images(self.ICON_STATE_PRESSED))
            self._icon_event_box.hide()
            self._icon_event_box.show()
            return True
        return False
    
    def mouse_out_callback(self, widget, event):
        self._icon_event_box.set_images(self.get_images(self.ICON_STATE_NORMAL))
        self._icon_event_box.hide()
        self._icon_event_box.show()
        return True
        
    def mouse_over_callback(self, widget, event):
        self._icon_event_box.set_images(self.get_images(self.ICON_STATE_MOUSEOVER))
        self._icon_event_box.hide()
        self._icon_event_box.show()
        return True

    def set_shortcut(self, shortcut):
        self._shortcut = shortcut
        self._identifier = shortcut.name()
        self._label_event_box._label.set_text(shortcut.name())