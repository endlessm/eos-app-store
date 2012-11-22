from shortcut.desktop_shortcut import DesktopShortcut
from eos_util import image_util
import gtk

class BugsAndFeedbackShortcut(DesktopShortcut):

    def __init__(self, label_text, callback):
        super(BugsAndFeedbackShortcut, self).__init__(label_text)
        
        self._callback = callback
        
        self._normal_text = label_text
        
        self._event_box.connect("button-press-event", self.mouse_press_callback)

        self.show_all()
        
    def mouse_press_callback(self, widget, event):
        if event.button == 1:# and event.type == gtk.gdk._2BUTTON_PRESS:
            self._callback(widget, event)
            return True
        return False
    
    def remove_shortcut(self):
        if self.parent:
            self.parent.remove(self)
    
    def get_images(self):
        return [Image.from_name("endless-shortcut-well.png"),Image.from_name("endless-shortcut-background.png"),Image.from_name("endless-feedback.png"), Image.from_name("endless-shortcut-foreground.png")]
