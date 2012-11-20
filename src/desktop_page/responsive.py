import gtk
from eos_widgets.image_eventbox import ImageEventBox


class Button(ImageEventBox):

    @classmethod
    def align_it(cls, button, xalign=0.5, yalign=0.5, xscale=0.0, yscale=0.0):
        align = gtk.Alignment(xalign, yalign, xscale, yscale)
        align.add(button)
        return align

    def __init__(self, normal=(), hover=(), down=(), select=(), invisible=False):
        self.normal = normal
        self.hover = hover
        self.down = down
        self.select = select
        self.is_selected = False
        self._set_last_images(self.normal)
        self._on_clicked = None
        self._invisible = invisible
        self.set_invisible(self._invisible)
        super(Button, self).__init__(self.normal)

        self.connect("button_press_event", self.button_press_event)
        self.connect("button_release_event", self.button_release_event)
        self.connect("enter_notify_event", self.enter_notify_event)
        self.connect("leave_notify_event", self.leave_notify_event)
        self.set_events(gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.LEAVE_NOTIFY_MASK
                            | gtk.gdk.ENTER_NOTIFY_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.BUTTON_RELEASE_MASK
                            )

    def connect(self, signal, callback):
        if signal == "clicked":
            self._on_clicked = callback
        else:
            super(Button, self).connect(signal, callback)

    def _set_last_images(self, images):
        self._last_images = images

    def _get_last_images(self):
        return self._last_images

    def set_invisible(self, value):
        self._invisible = value

    def display(self):
        if self._invisible:
            self.set_images(())
        self.hide()
        self.show()

    def selected(self):
        self.is_selected = True
        self.set_images(self.select)
        self._set_last_images(self.select)
        self.display()

    def unselected(self):
        self.is_selected = False
        self.set_images(self.normal)
        self._set_last_images(self.normal)
        self.display()

    def button_press_event(self, widget, event):
        self.set_images(self.down)
        self.display()
        if self._on_clicked is not None:
            self._on_clicked(widget)

    def button_release_event(self, widget, event):
        self.set_images(self._get_last_images())
        self.display()

    def enter_notify_event(self, widget, event):
        if not self.is_selected:
            self.set_images(self.hover)
            #self._set_last_images(self.hover)
            self.display()

    def leave_notify_event(self, widget, event):
        #self.set_images(self.normal)
        #self._set_last_images(self.normal)
        if not self.is_selected:
            self.set_images(self._get_last_images())
            self.display()
