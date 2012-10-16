import math
import sys
import gettext

import gtk
import gobject
from gtk import gdk

from util import image_util
from shortcut.application_shortcut import ApplicationShortcut
from feedback_module.feedback_response_dialog_view import FeedbackResponseDialogView
from feedback_module.bugs_and_feedback_popup_window import BugsAndFeedbackPopupWindow
from shortcut.folder_shortcut import FolderShortcut
from shortcut.separator_shortcut import SeparatorShortcut
from folder.folder_window import OpenFolderWindow
from notification_panel.notification_panel import NotificationPanel
from taskbar_panel.taskbar_panel import TaskbarPanel

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window):
    _padding = 100
    _app_shortcuts = {}

    def __init__(self):
        gtk.Window.__init__(self)
        
        width, height = self._get_net_work_area()
        self.resize(width, height)
        self.set_can_focus(False)
        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DESKTOP) #@UndefinedVariable
        self.set_decorated(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.unfocus_widget)
        self.connect('destroy', lambda w: gtk.main_quit())
        
        # The following prevents propagation of signals that close
        # the dektop (<Alt>F4)
        self.connect('delete-event', lambda w, e: True)

        self.maximize()
        self.show()
        self.set_app_paintable(True)
        
        # -----------WORKSPACE-----------
        
        self._align = gtk.Alignment(0.5, 0.5, 0, 0)
        
        self._taskbar_panel = TaskbarPanel(width)
        self._taskbar_panel.connect('feedback-clicked', lambda w: self._feedback_icon_clicked_callback())
        
        self._notification_panel = NotificationPanel(self)

        taskbar_alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        taskbar_alignment.add(self._taskbar_panel)
        
        # Main window layout
        self._desktop = gtk.VBox(False, 2)
        self._desktop.pack_start(self._notification_panel, False, True, 0)
        self._desktop.pack_start(self._align, True, False, 0)
        self._desktop.pack_end(taskbar_alignment, False, True, 0)
        
        self.add(self._desktop)
        self.show_all()
        
        self._max_icons_in_row = self._calculate_max_icons()
    
        screen = gtk.gdk.Screen() #@UndefinedVariable
        screen.connect('size-changed', lambda s: self._set_background(self.BACKGROUND_NAME))
        
    def unfocus_widget(self, widget, event):
        widget.set_focus(None)
        self.close_folder_window()
        self._notification_panel.close_settings_plugin_window()

    def set_presenter(self, presenter):
        self._presenter = presenter
        self._taskbar_panel.connect('launch-search', lambda w, s: self._presenter.launch_search(s))

    def get_presenter(self):
        return self._presenter
    
    def set_background_pixbuf(self, pixbuf):
        width, height = self._get_net_work_area()
#        pixbuf = image_util.load_pixbuf(background_name)
        
        sized_pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR) #@UndefinedVariable
        pixmap, mask = sized_pixbuf.render_pixmap_and_mask()
        
        del sized_pixbuf
        del pixbuf
        
        self.window.set_back_pixmap(pixmap, False)
        del pixmap
        del mask
        
        self.window.invalidate_rect((0, 0, width, height), False)

    def populate_popups(self, all_applications):
        self.popup = gtk.Menu()
        apps_menu = gtk.MenuItem(_("Apps"))
        if (len(all_applications) == 0):
            apps_menu.set_sensitive(False)
        else:
            sub_menu = gtk.Menu()
            for item in all_applications:
                menu_item = gtk.MenuItem(item.display_name())
                menu_item.item = item
                menu_item.connect("button-release-event", lambda w, e: self._presenter.add_item(w.item))
                sub_menu.add(menu_item)
            apps_menu.set_submenu(sub_menu)
        
        website_menu = gtk.MenuItem(_("Websites"))
        folder_menu = gtk.MenuItem(_("Folder"))
        
        website_menu.set_sensitive(False) 
        folder_menu.set_sensitive(False) 
         
        self.popup.add(apps_menu)
        self.popup.add(website_menu) 
        self.popup.add(folder_menu)
        
    def refresh(self, shortcuts):
        self._folder_shortcuts = {}
        for shortcut in shortcuts:

            if shortcut.key() not in self._app_shortcuts:
                if shortcut.has_children():
                    app_shortcut = FolderShortcut(shortcut, self._folder_icon_clicked_callback)
                else:
                    app_shortcut = ApplicationShortcut(shortcut)
                
                self._app_shortcuts[shortcut.name()] = app_shortcut
        self._shorcuts_buffer = [shortcut.name() for shortcut in shortcuts]
        self._redraw(self._shorcuts_buffer)
                
        self._align.show()

    def _redraw(self, icon_data):
        self._remove_all()
        
        child = self._align.get_child()
        if child:
            child.parent.remove(child)
            
        icon_container = gtk.VBox()
        icon_container.show()
        icon_container.set_spacing(30)
                
        items = [self._app_shortcuts[key] for key in icon_data]
        index = 0
        step = int(self._max_icons_in_row)
        while index < len(items) + 1:
            row = self._create_row(items[index:(step + index)])
            icon_container.add(row)
            index += step
            
        self._align.add(icon_container)        
        self._align.show()
        
    def _add_icon_clicked_callback(self, widget, event):
        self.popup.show_all()
        self.popup.popup(None, None, None, event.button, event.time)

            
    def _feedback_submitted(self, widget):
        self._presenter.submit_feedback(self._feedback_popup.get_text(), self._feedback_popup.is_bug())
        self._feedback_popup.destroy()
        self._show_feedback_thank_you_message()
        
    def _show_feedback_thank_you_message(self):     
        #spawn wait indicator
        self._feedback_thank_you_dialog = FeedbackResponseDialogView()
        self._feedback_thank_you_dialog.show()
        gobject.timeout_add(3000, self._feedback_thanks_close)
        
    def _feedback_thanks_close(self):
        self._feedback_thank_you_dialog.destroy()
        return False
    
    # Show popup
    def _feedback_icon_clicked_callback(self):
        self._feedback_popup = BugsAndFeedbackPopupWindow(self, self._feedback_submitted)
        self._feedback_popup.show()
        
    def hide_folder_window(self):
        if hasattr(self, '_folder_window') and self._folder_window:
            self._folder_window.hide()
            
    def close_folder_window(self):
        if hasattr(self, '_folder_window') and self._folder_window:
            self._folder_window.destroy()
            self._folder_window = None
            
    def show_folder_window(self, shortcut):
        self.close_folder_window()
        self._folder_window = OpenFolderWindow(
            self, 
            self._presenter.activate_item, 
            shortcut, 
            self._dnd_begin
            ) 
        self._folder_window.show()
    
    def show_folder_window_by_name(self, shortcut_name):
        shortcut = self._presenter.get_shortcut_by_name(shortcut_name)
        if shortcut is not None:
            self.show_folder_window(shortcut)
        
    # Show folder content
    def _folder_icon_clicked_callback(self, widget, event, shortcut):
        self.close_folder_window()
        self.show_folder_window(shortcut)
        
    def _remove_all(self):
        for item in self._app_shortcuts.values():
            item.remove_shortcut()
        
    def _create_row(self, items):
        row = gtk.HBox()
        row.show()
        
        sep_last = SeparatorShortcut()
        sep_last.connect("application-shortcut-move", self._rearrange_shortcuts)
        row.pack_start(sep_last, False, False, 0)
        for item in items:
            if isinstance(item, ApplicationShortcut):
                item.connect("application-shortcut-rename", lambda w, shortcut, new_name: self._presenter.rename_item(shortcut, new_name))
                item.connect("application-shortcut-activate", lambda w, app_key, params: self._presenter.activate_item(app_key, params))
                item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
                item.show()
                
            elif isinstance(item, FolderShortcut):
                item.connect("folder-shortcut-activate", self._folder_icon_clicked_callback)
                item.connect("folder-shortcut-relocation", self._relocation_callback)
                item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
                item.show()
                
            if item.parent != None:
                print >> sys.stderr, "Item has parent!", item
            row.pack_start(item, False, False, 0)
            sep_new = SeparatorShortcut()
            sep_new.connect("application-shortcut-move", self._rearrange_shortcuts)
            row.pack_start(sep_new, False, False, 0)
            sep_last.set_right_separator(sep_new)
            sep_last.set_right_widget(item)
            sep_new.set_left_separator(sep_last)
            sep_new.set_left_widget(item)
            sep_last = sep_new
            
        return row
        
    def _dnd_begin(self, widget):
        self.hide_folder_window()
        
    def _relocation_callback(self, widget, source_shortcut, folder_shortcut):
        self._presenter.relocate_item(source_shortcut, folder_shortcut)
        
    def _rearrange_shortcuts(self, widget, source_shortcut, left_shortcut, 
            right_shortcut
            ):
        if source_shortcut.parent() is not None:
            self._relocation_callback(widget, source_shortcut, None)
            
        if right_shortcut is not None:
            if source_shortcut.name() in self._shorcuts_buffer:
                self._shorcuts_buffer.remove(source_shortcut.name())
            index = self._shorcuts_buffer.index(right_shortcut.name())
            self._shorcuts_buffer.insert(index, source_shortcut.name())
            self._presenter.move_item(self._shorcuts_buffer)
            return
            
        if left_shortcut is not None:
            if source_shortcut.name() in self._shorcuts_buffer:
                self._shorcuts_buffer.remove(source_shortcut.name())
            index = self._shorcuts_buffer.index(left_shortcut.name()) + 1
            if index < len(self._shorcuts_buffer):
                self._shorcuts_buffer.insert(index, source_shortcut.name())
            else:
                self._shorcuts_buffer.append(source_shortcut.name())
            self._presenter.move_item(self._shorcuts_buffer)
        
    def _calculate_max_icons(self):
        width = self._get_net_work_area()[0]

        available_width = width - (self._padding * 2)        
        return math.floor(available_width / 125)
    
    def _get_net_work_area(self):
        """this section of code gets the net available area on the window (i.e. root window - panels)"""
        self.realize()
        screen = gtk.gdk.Screen() #@UndefinedVariable
        monitor = screen.get_monitor_at_window(self.window)
        geometry = screen.get_monitor_geometry(monitor)
        width = geometry.width
        height = geometry.height
                
        return width, height
    
    def main(self):
        gobject.threads_init()
        gtk.threads_init()
        gtk.main()
