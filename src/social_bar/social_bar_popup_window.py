import gtk
from eos_widgets.image_eventbox import ImageEventBox
from eos_util.image import Image
from eos_widgets.desktop_transparent_window import DesktopTransparentWindow


class SocialBarPopupWindow():
    def __init__(self, parent):
        self._width = 256
        self._height = 225
        
        # Since the TransparentWindow class does not have an option to force centered,
        # for now let's manually calculate the centered position
        # self._window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        desktop_size = parent.get_size()
        x = (desktop_size[0] - self._width) / 2
        y = (desktop_size[1] - self._height) / 2
        self._window = DesktopTransparentWindow(parent, (x, y), (self._width, self._height))

        self._fancy_container = ImageEventBox([Image.from_name("feedback-background.png")])
        self._fancy_container.set_size_request(self._width,self._height)
        self._center = gtk.Alignment(.5,.3,0,0)
        
        self._close = ImageEventBox([Image.from_name("close.png")])
        self._close.set_size_request(24,24)
        self._close.connect("button-release-event", lambda w, e: self.destroy())
        
        self._container = gtk.VBox(False)
        
        self._close_box = gtk.HBox(False)
        self._close_box.pack_end(self._close, False, False, 0)
        
        self._container.pack_start(self._close_box, True, False, 0)
        
        self._toggle_box = gtk.HBox(True)
        self._toggle_box.set_size_request(75,30)
        
        self._container.pack_start(self._toggle_box, True, True, 5)
        
        self._text = gtk.TextView()
        self._text.set_wrap_mode(gtk.WRAP_WORD)
        self._text.set_size_request(200,80)
        self._text.set_editable(True)
        self._text_buffer = gtk.TextBuffer()
        self._text_buffer.set_text("This is just a place holder.  The social bar icon was clicked.")
        self._text.set_buffer(self._text_buffer)
        
        self._text_holder = gtk.Alignment(.5,.5,0.9,0.8)
        self._text_holder.add(self._text)
        self._container.pack_start(self._text_holder, True, True,10)
              
        self._center.add(self._container)
        self._fancy_container.add(self._center)

        self._window.add(self._fancy_container)
        self._window.show_all()
        
    def _set_widget_text(self, widget, text):
        widget.get_children()[0].set_markup('<span foreground="#505050" size="x-small">' + text + '</span>')
            
    def show(self):
        self._window.show_all()
        
    def destroy(self):
        self._window.destroy()
