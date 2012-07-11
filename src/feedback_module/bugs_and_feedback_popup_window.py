import gtk
import gettext
from util.image_eventbox import ImageEventBox
from util import image_util
from util.transparent_window import TransparentWindow

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class BugsAndFeedbackPopupWindow():
    
    def __init__(self, callback):
        
        self._width = 400
        self._height = 400
        
        self._window = TransparentWindow()
        self._window.set_size_request(self._width,self._height)
        self._window.set_title(_("Bugs And Feedback"))
        self._window.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self._fancy_container = ImageEventBox((image_util.image_path("endless-feedback-background.png"),))
        
        self._fancy_container.set_size_request(self._width,self._height)
#        self._fancy_container.set_visible_window(False)
        self._center = gtk.Alignment(.5,.5,0,0)
        
        self._close = ImageEventBox((image_util.image_path("endless-close.png"),))
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        
        self._container = gtk.VBox(False)
        self._container.set_size_request(350,400)
        self._container.set_spacing(5)
        
        self._close_box = gtk.HBox(False)
        self._close_box.pack_end(self._close, False, False, 0)
        
        self._container.pack_start(self._close_box, False, False, 5)
        
        self._toggle_box = gtk.HBox(False)
        self._toggle_box.set_size_request(75,50)
        self._bug_button = gtk.RadioButton(None, _("Report a Bug"))
        self._bug_button.set_size_request(50,100)
        self._bug_button.set_mode(False)
        self._toggle_box.pack_start(self._bug_button, True, True)
        self._feedback_button = gtk.RadioButton(self._bug_button, _("Give us feedback"))
        self._feedback_button.set_size_request(50,100)
        self._feedback_button.set_mode(False)
        self._toggle_box.pack_start(self._feedback_button, True, True)
        
        self._container.pack_start(self._toggle_box, False, False, 5)
        
        self._text = gtk.TextView()
        self._text.set_size_request(100,200)
        self._text.set_wrap_mode(gtk.WRAP_WORD)
        self._text_buffer = gtk.TextBuffer()
        self._text_buffer.set_text(_("Please let us know how the problem occured and we will resolve it as soon as possible."))
        self._text.set_buffer(self._text_buffer)
        self._container.pack_start(self._text, False, False,5)
              
        self._button = gtk.Button()
        self._button.set_label(_("SUBMIT"))
        self._button.set_size_request(100, 50)
        self._button.connect("button-release-event",lambda w, e: callback(w))
        self._container.pack_start(self._button, False, False,5)
        
              
        self._center.add(self._container)
        self._fancy_container.add(self._center)

        self._window.add(self._fancy_container)
        self._window.show_all()
        

    def get_text(self):
        b = self._text.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), False)
    
    def is_bug(self):
        return self._bug_button.get_active()
    
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
