import gtk
import operator

class PaddingWidget(gtk.Alignment):
    def __init__(self, xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0, outline=True):
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
        window_coords = self.window.get_root_origin()
        widget_coords = self.translate_coordinates(self.get_toplevel(), 0, 0)
        absolute_coords = tuple(map(operator.add, window_coords, widget_coords))

        widget_size = self.get_size_request()
        if widget_size == (-1, -1):
            widget_size = (self.allocation.width,self.allocation.height)

        x = absolute_coords[0]
        y = absolute_coords[1]

        # For each image to be composited
        cr.rectangle(x,y,widget_size[0],widget_size[1])
        cr.set_source_rgb(1,0,0) #Red
        cr.set_line_width(1)

        cr.stroke()

