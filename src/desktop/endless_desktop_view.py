import math
import sys
import gettext

import gtk
import gobject
from gtk import gdk

from eos_util import image_util
from shortcut.application_shortcut import ApplicationShortcut
from feedback_module.feedback_response_dialog_view import FeedbackResponseDialogView
from feedback_module.bugs_and_feedback_popup_window import BugsAndFeedbackPopupWindow
from removal_module.removal_confirmation_popup_window import RemovalConfirmationPopupWindow
from shortcut.folder_shortcut import FolderShortcut
from shortcut.separator_shortcut import SeparatorShortcut
from shortcut.add_remove_shortcut import AddRemoveShortcut
from desktop_page.desktop_page import DesktopPage
from folder.folder_window import OpenFolderWindow
from folder.folder_window import FULL_FOLDER_ITEMS_COUNT
from notification_panel.notification_panel import NotificationPanel
from taskbar_panel.taskbar_panel import TaskbarPanel

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window):
    MAX_ICONS_IN_ROW = 7
    HORIZONTAL_SPACING = 60
    VERTICAL_SPACING = 60
    LABEL_HEIGHT = 10
    _padding = 100
    _app_shortcuts = {}

    def __init__(self):
        gtk.Window.__init__(self)
        self._app_shortcuts = []
        
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
        
        self._align = gtk.Alignment(1.0, 1.0, 1.0, 1.0)
        
        self._taskbar_panel = TaskbarPanel(width)
        self._taskbar_panel.connect('feedback-clicked', lambda w: self._feedback_icon_clicked_callback())
        
        self._notification_panel = NotificationPanel(self)

        taskbar_alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        taskbar_alignment.add(self._taskbar_panel)
        
        # Main window layout
        self._desktop = gtk.VBox(False, 2)
        self._desktop.pack_start(self._notification_panel, False, False, 0)
        
        # btn = gtk.Button()
        # btn.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(35,50000,1000))
        # btn.show()
        # self._desktop.pack_start(btn, True, False, 0)
        
        self._desktop.pack_start(self._align, True, True, 0)
        self._desktop.pack_end(taskbar_alignment, False, False, 0)
        
        self.add(self._desktop)
        self.show_all()
        
        #self._max_icons_in_row = self._calculate_max_icons()
        self._max_icons_in_row = self.MAX_ICONS_IN_ROW
        self._max_rows_in_page = 4
    
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
        
    def refresh(self, shortcuts, force=False):
            
        child = self._align.get_child()
        if child:
            child.parent.remove(child)
            child.destroy()
            
        DesktopPage.calc_pages(
            shortcuts, 
            create_row_callback = self._create_row, 
            reload_callback = self._page_change_callback, 
            max_items_in_row = self._max_icons_in_row, 
            max_rows_in_page = self._max_rows_in_page
            )
        desk_page = DesktopPage.get_current_page()
        desk_page.show()
        
        self._align.add(desk_page)
        desk_page.show()
        self._align.show()
        
    def _page_change_callback(self):
        self._presenter._page_change_callback()
        
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
        
    def _create_row(self, items, last_row=False):
    
        while len(self._app_shortcuts) > 0:
            w = self._app_shortcuts[0]
            w.destroy()
    
        row = gtk.HBox()
        row.show()
        
        sep_last = SeparatorShortcut(width=self.HORIZONTAL_SPACING/2)
        sep_last.connect("application-shortcut-move", self._rearrange_shortcuts)
        row.pack_start(sep_last, False, False, 0)
        
        for shortcut in items:
            if shortcut.has_children():
                item = FolderShortcut(shortcut, self._folder_icon_clicked_callback)
                item.connect("folder-shortcut-activate", self._folder_icon_clicked_callback)
                item.connect("folder-shortcut-relocation", self._relocation_callback)
                item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
                item.show()
            else:
                item = ApplicationShortcut(shortcut)
                item.connect("application-shortcut-rename", lambda w, shortcut, new_name: self._presenter.rename_item(shortcut, new_name))
                item.connect("application-shortcut-activate", lambda w, app_key, params: self._presenter.activate_item(app_key, params))
                item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
                item.show()
        #
            if item.parent != None:
                print >> sys.stderr, "Item has parent!", item
            row.pack_start(item, False, False, 0)
            sep_new = SeparatorShortcut(width=self.HORIZONTAL_SPACING/2)
            sep_new.connect("application-shortcut-move", self._rearrange_shortcuts)
            row.pack_start(sep_new, False, False, 0)
            sep_last.set_right_separator(sep_new)
            sep_last.set_right_widget(item)
            sep_new.set_left_separator(sep_last)
            sep_new.set_left_widget(item)
            sep_last = sep_new
        
        #Adding AddRemove icon at the end of row
        if last_row:
            add_remove = AddRemoveShortcut(callback=self.show_add_dialogue)
            add_remove.connect("application-shortcut-remove", self._delete_shortcuts)
            row.pack_start(add_remove, False, False, 0)
            add_remove.show()
        
        return row
        
    def _dnd_begin(self, widget):
        self.hide_folder_window()
        
    def _relocation_callback(self, widget, source_shortcut, folder_shortcut):
        # move on desktop
        if folder_shortcut is None:
            self._presenter.relocate_item(source_shortcut, folder_shortcut)
            return
    
        if len(folder_shortcut.children()) < FULL_FOLDER_ITEMS_COUNT:
            self._presenter.relocate_item(source_shortcut, folder_shortcut)
            
        
    def _rearrange_shortcuts(self, widget, source_shortcut, left_shortcut, 
            right_shortcut
            ):
        self._presenter.rearrange_shortcuts(
            source_shortcut, 
            left_shortcut, 
            right_shortcut
            )
            
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
    
    def show_add_dialogue(self, event_box, event):
        print "Should show add dialogue..."
        
    def _delete_shortcuts(self, widget, sc_deleted):
        self._presenter.delete_shortcut(sc_deleted)
    
    def main(self):
        gobject.threads_init()
        gtk.threads_init()
        gtk.main()
