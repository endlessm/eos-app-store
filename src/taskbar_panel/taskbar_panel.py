import gtk
import cairo
from gtk import gdk
import gobject

from eos_util import image_util
from eos_util.image_util import load_pixbuf
from application_list_plugin import ApplicationListPlugin
from taskbar_shortcut import TaskbarShortcut
from social_bar.social_bar_plugin import SocialBarPlugin
from browser_button import BrowserButton
from browser_button_constants import BrowserButtonConstants
from notification_panel.notification_panel import NotificationPanel

class TaskbarPanel(gtk.EventBox):

    ICON_SIZE = BrowserButtonConstants.ICON_SIZE

    def __init__(self, parent, width):
        super(TaskbarPanel, self).__init__()
        self._parent = parent
        self.set_visible_window(False)
        self.set_app_paintable(True)
        self.connect('expose-event', self._redraw)

        taskbar_panel_items = self._align_taskbar()

        browser_button = self._setup_browser_button_on_taskbar()
        application_list_plugin_holder = self._setup_apps_on_taskbar()

        self._draw_taskbar(width, taskbar_panel_items, browser_button, application_list_plugin_holder)

        self.add(self._taskbar_panel)

    def _setup_browser_button_on_taskbar(self):
        browser_button_holder = gtk.Alignment(0.5, 0.5, 0, 1.0)
        browser_button_holder.set_padding(0, 0, 2, 0)
        browser_button = BrowserButton().get_button()
        browser_button_holder.add(browser_button)
        return browser_button_holder

    def _draw_taskbar(self, width, taskbar_panel_items, browser_button, application_list_plugin_holder):
        self._raw_taskbar_bg_pixbuf = load_pixbuf(image_util.image_path('bottom-shadow.png'))
        self._taskbar_bg_pixbuf = self._raw_taskbar_bg_pixbuf.scale_simple(width, 38, gdk.INTERP_TILES)
        del self._raw_taskbar_bg_pixbuf
        taskbar_panel_items.pack_start(browser_button, False, True, 0)
        taskbar_panel_items.pack_start(application_list_plugin_holder, False, True, 0)

        display_on_right = lambda plugin: taskbar_panel_items.pack_end(plugin, False, False, 10)
        self._notification_panel = NotificationPanel(self)
        display_on_right(self._notification_panel)

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
    
    def close_settings_plugin_window(self):
        self._notification_panel.close_settings_plugin_window()
    
    

