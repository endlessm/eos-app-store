import gtk
import cairo
from gtk import gdk
import gobject

from osapps.app_launcher import AppLauncher
from notification_panel.feedback_plugin import FeedbackPlugin
from search.search_box import SearchBox
from util import image_util
from util.image_util import load_pixbuf
from application_list_plugin import ApplicationListPlugin

class TaskbarPanel(gtk.EventBox):
    __gsignals__ = {
                    'feedback-clicked': (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                                         gobject.TYPE_NONE,
                                         ()),
                    'launch-search': (gobject.SIGNAL_RUN_FIRST, #@UndefinedVariable
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)), 
    }
    
    ICON_SIZE = 24
    
    def __init__(self, width):
        super(TaskbarPanel, self).__init__()
        self.set_visible_window(False)
        self.set_app_paintable(True)
        self.connect('expose-event', self._redraw)
        self.connect('configure-event', self._redraw)
        
        self._taskbar_panel = gtk.Alignment(0.5, 0.5, 1.0, 0)
        self._taskbar_panel.set_padding(0, 2, 0, 0)
        
        taskbar_panel_items = gtk.HBox(False)
        self._taskbar_panel.add(taskbar_panel_items)

        self._textbox = SearchBox()
        self._textbox.connect('launch-search', lambda w, s: self.emit('launch-search', s))
        
        application_list_plugin = ApplicationListPlugin(self.ICON_SIZE)
        
        
        feedback_plugin = FeedbackPlugin(self.ICON_SIZE)
        feedback_plugin.connect('button-press-event', lambda w, e: self.emit('feedback-clicked'))
        
        self._raw_taskbar_bg_pixbuf = load_pixbuf(image_util.image_path('taskbar.png'))
        self._taskbar_bg_pixbuf = self._raw_taskbar_bg_pixbuf.scale_simple(width, 38, gdk.INTERP_TILES)
        del self._raw_taskbar_bg_pixbuf
         
        taskbar_panel_items.pack_start(self._textbox, False, False, 10)
        taskbar_panel_items.pack_start(application_list_plugin, False, False, 10)
        taskbar_panel_items.pack_end(feedback_plugin, False, False, 10)
        
        self.add(self._taskbar_panel)

    def _redraw(self, widget, event):
        cr = widget.window.cairo_create()
        x,y = self.window.get_origin()
        
        self.draw(cr, x,y)
        
        return False
        
    def draw(self, cr, x, y):
        vertical_offset = self.get_parent_window().get_size()[1] - self._taskbar_bg_pixbuf.get_height()

        cr.set_source_pixbuf(self._taskbar_bg_pixbuf, 0, vertical_offset)
        cr.paint()
        
        return True
        