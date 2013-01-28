import gtk
import cairo
from gtk import gdk
import gobject

from feedback.feedback_plugin import FeedbackPlugin
from eos_util import image_util
from eos_util.image_util import load_pixbuf
from application_list_plugin import ApplicationListPlugin
from taskbar_shortcut import TaskbarShortcut
from social_bar.social_bar_plugin import SocialBarPlugin

class TaskbarPanel(gtk.EventBox):

    ICON_SIZE = 32

    def __init__(self, parent, width):
        super(TaskbarPanel, self).__init__()
        self._parent = parent
        self.set_visible_window(False)
        self.set_app_paintable(True)
        self.connect('expose-event', self._redraw)

        taskbar_panel_items = self._align_taskbar()

        application_list_plugin_holder = self._setup_apps_on_taskbar()
        feedback_plugin = self._setup_feedback_icon_on_taskbar()

        self._draw_taskbar(width, taskbar_panel_items, application_list_plugin_holder, feedback_plugin)

        self.add(self._taskbar_panel)

    def _draw_taskbar(self, width, taskbar_panel_items, application_list_plugin_holder, feedback_plugin):
        self._raw_taskbar_bg_pixbuf = load_pixbuf(image_util.image_path('taskbar.png'))
        self._taskbar_bg_pixbuf = self._raw_taskbar_bg_pixbuf.scale_simple(width, 38, gdk.INTERP_TILES)
        del self._raw_taskbar_bg_pixbuf
        taskbar_panel_items.pack_start(application_list_plugin_holder, False, True, 0)

        display_on_right = lambda plugin: taskbar_panel_items.pack_end(plugin, False, False, 10)
        self._setup_social_bar_icon_on_taskbar().display(display_on_right )
        display_on_right(feedback_plugin)

    def _setup_feedback_icon_on_taskbar(self):
        feedback_plugin = FeedbackPlugin(self._parent, self.ICON_SIZE)
        return feedback_plugin

    def _setup_social_bar_icon_on_taskbar(self):
        social_bar_plugin = SocialBarPlugin(self._parent, self.ICON_SIZE)
        return TaskbarShortcut(social_bar_plugin, social_bar_plugin.get_path())

    def _align_taskbar(self):
        self._taskbar_panel = gtk.Alignment(0.5, 0.5, 1.0, 0)
        self._taskbar_panel.set_padding(0, 2, 0, 0)
        taskbar_panel_items = gtk.HBox(False)
        self._taskbar_panel.add(taskbar_panel_items)
        return taskbar_panel_items

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

