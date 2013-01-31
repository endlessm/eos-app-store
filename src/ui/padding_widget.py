import gtk

class PaddingWidget(gtk.Alignment):

    def __init__(self, xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0, outline=False):
        super(PaddingWidget, self).__init__(xalign, yalign, xscale, yscale)
        self.connect("expose-event", self.do_expose_event)
        self._outline = outline

    @property
    def outline(self):
        return self._outline

    @outline.setter
    def outline(self, value):
        self._outline = value

    def do_expose_event(self, widget, event):
        if self._outline:
            self.draw(widget.window.cairo_create())
        return False

    def draw(self, cr):
        # Get the size and location of the region where the image is to be drawn
        area = self.get_allocation()
        x = area.x
        y = area.y
        w, h = self.size_request()

        # For each image to be composited
        cr.rectangle(x,y,w,h)
        cr.set_source_rgb(1,0,0) #Red
        cr.set_line_width(1)

        cr.stroke()

