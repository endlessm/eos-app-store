import gtk

from eos_util.image import Image
from desktop_page.button import Button

class DesktopNavButton(gtk.Alignment):
    def __init__(self, img_id, on_click):
        super(DesktopNavButton, self).__init__(0.5, 0.5, 0.0, 0.0)

        hover_image = "button_arrow_desktop_" + img_id + "_hover.png"
        pressed_image = "button_arrow_desktop_" + img_id + "_down.png"
        self._button = Button(
                normal=(), 
                hover=(Image.from_name(hover_image), ), 
                down=(Image.from_name(pressed_image), ), 
                invisible=True)
        self._button.connect("clicked", on_click)
        self._button.set_size_request(50, 550)

        self.add(self._button)

    def set_is_visible(self, is_visible):
        self._button.set_invisible(not is_visible)
        self._button.display()
