import gtk
import gobject
import gettext

from util import image_util
from util.image_util import load_pixbuf

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class SearchBox(gtk.EventBox):
    HEIGHT = 30
    WIDTH = 234
    LEFT_PADDING = 10
    RIGHT_MARGIN = 33
    BOTTOM_MARGIN = 13

    DEFAULT_TEXT = _("Enter Search or URL...")
    
    __gsignals__ = {
           "launch-search": (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                                    gobject.TYPE_NONE,
                                    (gobject.TYPE_PYOBJECT,)), 
    }
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.set_visible_window(False)
        
        self.connect('button-press-event', self.gain_focus)
        self._content = gtk.Fixed()
        
        self._label = SearchBoxLabel(self.DEFAULT_TEXT)
        self._label.set_size_request(self.WIDTH, self.HEIGHT)
        self._content.put(self._label, self.LEFT_PADDING, 0)
        
        self.add(self._content)
        self._content.show_all()

    def add_text_entry(self, text):
        self._text_view = gtk.TextView()
        self._text_buffer = self._text_view.get_buffer()
        self._text_view.set_wrap_mode(gtk.WRAP_NONE)
        self._text_view.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('#303030'))
        self._text_view.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#ffffff')) 

        self._text_view.set_size_request(self.WIDTH-self.RIGHT_MARGIN - SearchBoxLabel.LEFT_MARGIN, self.HEIGHT-self.BOTTOM_MARGIN)
        
        self._text_view.hide()

        self._text_view.connect("focus-out-event", lambda w, e: self._update_label(w))
        self._text_view.connect("key-press-event", self.handle_keystrokes)
        
        self._content.put(self._text_view, self._label.LEFT_MARGIN + self.LEFT_PADDING, self._label.TOP_MARGIN)
        
    def gain_focus(self, widget, event):
        if not(hasattr(self, "_text_view")):
            self.add_text_entry("")
            
        self._set_label_text("")
        self._text_view.show()
        self._text_view.grab_focus()
        return True

    def _set_label_text(self, text):
        self._label.set_text(text)

    def _update_label(self, widget):
        search_text = self._text_buffer.get_text(self._text_buffer.get_start_iter(), self._text_buffer.get_end_iter(), False)
        self._text_view.hide()
        if len(search_text) > 0:
            self._set_label_text(search_text)
        else:
            self._set_label_text(self.DEFAULT_TEXT)
        
    def _launch_browser(self, widget):
        search_text = self._text_buffer.get_text(self._text_buffer.get_start_iter(), self._text_buffer.get_end_iter(), False)
        self._text_buffer.set_text("")
        self._text_view.hide()
        self._set_label_text(self.DEFAULT_TEXT)
        
        self.emit("launch-search", search_text)
    
    def handle_keystrokes(self, widget, event):
        if(event.keyval == gtk.keysyms.Escape):
            self._text_buffer.set_text("")
            self._text_view.hide()
            self._set_label_text(self.DEFAULT_TEXT)
            return True
        elif(event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter):
            self._launch_browser(widget)
            return True
        return False

class SearchBoxLabel(gtk.Fixed):
    TOP_MARGIN = 5
    LEFT_MARGIN = 40
    RIGHT_PADDING = 16
    RIGHT_MARGIN = 10
    
    def __init__(self, default_text):
        gtk.Fixed.__init__(self)
        
        self._search_bg_pixbuf = load_pixbuf(image_util.image_path("text_frame_normal.png"))
        self._internet_pixbuf = load_pixbuf(image_util.image_path("button_browser_normal.png"))
        
        self._image = gtk.Image()
        self._image.set_from_pixbuf(self._search_bg_pixbuf)
        self.put(self._image, 0, 0)
        
        self._internet_image = gtk.Image()
        self._internet_image.set_from_pixbuf(self._internet_pixbuf)
        self.put(self._internet_image, 5, 2)

        self._label = gtk.Label()
        self._label.set_text(default_text)
        self._label.set_justify(gtk.JUSTIFY_LEFT)
        self._label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#303030'))
        alignment = gtk.Alignment(0.0, 0.5, 0.0, 0.0)
        alignment.add(self._label)
        
        self.put(alignment, self.LEFT_MARGIN, self.TOP_MARGIN)
        
    def set_text(self, text):
        max_width = self._search_bg_pixbuf.get_width() - (self.LEFT_MARGIN + self.RIGHT_MARGIN)

        shown_text = ""
        for letter in text:
            shown_text += letter
            layout = self._label.create_pango_layout(shown_text)
            text_size = layout.get_pixel_size()[0] 
            if text_size + self.RIGHT_PADDING >= max_width:
                shown_text += "..." 
                break
            
        self._label.set_text(shown_text)
        
