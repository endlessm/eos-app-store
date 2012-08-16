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
        
        taskbar_panel_items = self._align_taskbar()

        searchbox_holder = self._setup_searchbar_on_taskbar()
        application_list_plugin_holder = self._setup_apps_on_taskbar()
        feedback_plugin = self._setup_feedback_icon_on_taskbar()
        
        self._draw_taskbar(width, taskbar_panel_items, application_list_plugin_holder, searchbox_holder, feedback_plugin)
        
        self.add(self._taskbar_panel)

    def _draw_taskbar(self, width, taskbar_panel_items, application_list_plugin_holder, searchbox_holder, feedback_plugin):
        self._raw_taskbar_bg_pixbuf = load_pixbuf(image_util.image_path('glass_taskbar.png'))
        self._taskbar_bg_pixbuf = self._raw_taskbar_bg_pixbuf.scale_simple(width, 38, gdk.INTERP_TILES)
        del self._raw_taskbar_bg_pixbuf
        taskbar_panel_items.pack_start(searchbox_holder, False, False, 0)
        taskbar_panel_items.pack_start(application_list_plugin_holder, False, True, 0)
        taskbar_panel_items.pack_end(feedback_plugin, False, False, 10)


    def _setup_feedback_icon_on_taskbar(self):
        feedback_plugin = FeedbackPlugin(self.ICON_SIZE)
        feedback_plugin.connect('button-press-event', lambda w, e:self.emit('feedback-clicked'))
        return feedback_plugin


    def _align_taskbar(self):
        self._taskbar_panel = gtk.Alignment(0.5, 0.5, 1.0, 0)
        self._taskbar_panel.set_padding(0, 2, 0, 0)
        taskbar_panel_items = gtk.HBox(False)
        self._taskbar_panel.add(taskbar_panel_items)
        return taskbar_panel_items


    def _setup_searchbar_on_taskbar(self):
        self._searchbox_holder = gtk.Alignment(0.5, 0.5, 0, 1.0)
        self._searchbox_holder.set_padding(0, 0, 2, 0)
        self._searchbox = SearchBox()
        self._searchbox.connect('launch-search', lambda w, s:self.emit('launch-search', s))
        self._searchbox_holder.add(self._searchbox)
        return self._searchbox_holder 

    def _setup_apps_on_taskbar(self):
        application_list_plugin_holder = gtk.Alignment(0.5, 0.5, 0, 1.0)
        application_list_plugin_holder.set_padding(0, 0, 2, 0)
        application_list_plugin = ApplicationListPlugin(self.ICON_SIZE)
        application_list_plugin_holder.add(application_list_plugin)
        return application_list_plugin_holder


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
        