import math
import sys
import gettext

import gtk
import gobject
from gtk import gdk

from util import image_util, screen_util
from shortcut.bugs_and_feedback_shortcut import BugsAndFeedbackShortcut
from shortcut.application_shortcut import ApplicationShortcut
from feedback_module.feedback_response_dialog_view import FeedbackResponseDialogView
from search.search_box import SearchBox
from feedback_module.bugs_and_feedback_popup_window import BugsAndFeedbackPopupWindow
from shortcut.folder_shortcut import FolderShortcut
from folder.folder_window import OpenFolderWindow
from notification_panel.notification_panel import NotificationPanel

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])

class EndlessDesktopView(gtk.Window):
    _padding = 100
    _app_shortcuts = {}

    def __init__(self):
        gtk.Window.__init__(self)
        #setting up screen and background
        width, height = self._get_net_work_area()
        self.resize(width, height)
        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DESKTOP) #@UndefinedVariable
        self.set_decorated(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.unfocus_widget)
        self.connect("destroy", lambda w: gtk.main_quit())
        self.maximize()
        self.show()
        self.set_app_paintable(True)
        
        self._set_background()
        
        self.align = gtk.Alignment(0.5, 0.5, 0, 0)
        
        self.panel = gtk.HBox(False,2)
        width, height = self._get_net_work_area()
        self._textbox = SearchBox(width, height, self)
        self.panel.pack_start(self._textbox, False, True, 0)

        self.notification_panel = NotificationPanel()
        
        # Main window layout
        self._vbox = gtk.VBox(False,2)
        self._vbox.pack_start(self.notification_panel, False, True, 0)
        self._vbox.pack_start(self.align, True, False, 0)
        self._vbox.pack_end(self.panel, False, True, 0)
        
        self.add(self._vbox)
        self.show_all()
        
        self._max_icons_in_row = self._calculate_max_icons()
    
        screen = gtk.gdk.Screen() #@UndefinedVariable
        screen.connect("size-changed", lambda s: self._set_background())
    
    def unfocus_widget(self, widget, event):
        widget.set_focus(None)
        self.hide_folder_window()

    def set_presenter(self, presenter):
        self._presenter = presenter
        
#        self._add_icon = AddRemoveShortcut(_("Add new"), self._add_icon_clicked_callback)
#        self._add_icon.connect("application-shortcut-remove", lambda w, e: self._add_icon.toggle_drag(False))
#        self._add_icon.connect("application-shortcut-remove", self._remove_icon)
        
#        self._feedback_icon = BugsAndFeedbackShortcut(_("Feedback"), self._feedback_icon_clicked_callback)
        self._textbox.connect("launch-search", lambda w, s: self._presenter.launch_search(s))

    def _set_background(self):
        width, height = self._get_net_work_area()
        pixbuf = image_util.load_pixbuf("background.png")
        
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
#            if shortcut.id() not in self._app_shortcuts:
            if shortcut.key() not in self._app_shortcuts:
                if shortcut.has_children():
                    app_shortcut = FolderShortcut(shortcut, self._folder_icon_clicked_callback)
                else:
                    app_shortcut = ApplicationShortcut(shortcut)
                
                self._app_shortcuts[shortcut.key()] = app_shortcut
        self._shorcuts_buffer = [shortcut.key() for shortcut in shortcuts]
        self._redraw(self._shorcuts_buffer)
                
#                self._app_shortcuts[shortcut.id()] = app_shortcut
#        self._shorcuts_buffer = [shortcut.id() for shortcut in shortcuts]
#        self._redraw(self._shorcuts_buffer)

        self.align.show()

#    def _redraw(self, icon_data):
#        pass

#TODO FIX ME ***************************************************************************************************
    def _redraw(self, icon_data):
        self._remove_all()
        
        child = self.align.get_child()
        if child:
            child.parent.remove(child)
            
        icon_container = gtk.VBox()
        icon_container.show()
        icon_container.set_spacing(30)
                
        items = [self._app_shortcuts[key] for key in icon_data] # + [self._feedback_icon] # + [self._add_icon]
#        items = [self._app_shortcuts[item_id] for item_id in icon_data] # + [self._feedback_icon] # + [self._add_icon]
        index = 0
        step = int(self._max_icons_in_row)
        while index < len(items) + 1:
            row = self._create_row(items[index:(step + index)])
            icon_container.add(row)
            index += step
            
        self.align.add(icon_container)        
        self.align.show()
        
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
    def _feedback_icon_clicked_callback(self, widget, event):
        self._feedback_popup = BugsAndFeedbackPopupWindow(self._feedback_submitted)
        self._feedback_popup.show()
        
    def hide_folder_window(self):
        if hasattr(self, '_folder_window') and self._folder_window:
            self._folder_window.destroy()
            self._folder_window = None
                
    # Show folder content
    def _folder_icon_clicked_callback(self, widget, event, shortcut):
        self.hide_folder_window()
        self._folder_window = OpenFolderWindow(self.window, self._presenter.activate_item, shortcut) 
        self._folder_window.show()
        
    def _remove_all(self):
        for item in self._app_shortcuts.values():
            item.remove_shortcut()
            
#        self._add_icon.remove_shortcut()
#        self._feedback_icon.remove_shortcut()
        
    def _create_row(self, items):
        row = gtk.HBox()
        row.show()
        
        for item in items:
            if isinstance(item, ApplicationShortcut):
                item.connect("application-shortcut-rename", lambda w, shortcut, new_name: self._presenter.rename_item(shortcut, new_name))
                item.connect("application-shortcut-activate", lambda w, app_key: self._presenter.activate_item(app_key))
                item.connect("application-shortcut-dragging-over", lambda w, s: self._insert_placeholder(s))
                item.connect("application-shortcut-drag", lambda w, state: self._add_icon.toggle_drag(state))
                item.connect("application-shortcut-move", lambda w: self._presenter.move_item(self._shorcuts_buffer))
                
                item.show()
                
            elif isinstance(item, FolderShortcut):
                item.connect("application-shortcut-activate", lambda w, app_id: self._presenter.activate_item(app_id))
                
                item.show()
                
            if item.parent != None:
                print >> sys.stderr, "Item has parent!", item
            row.pack_start(item, False, False, 30)
            
        return row
    
    def _insert_placeholder(self, s):
        moving = [x for x in self._shorcuts_buffer if self._app_shortcuts[x].is_moving()]
        
        if moving:
            for item in moving:
                new_index = self._shorcuts_buffer.index(s.id())
                
                self._shorcuts_buffer.remove(item)
                self._shorcuts_buffer.insert(new_index, item)
            
            self._redraw(self._shorcuts_buffer)
        
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
        gtk.main()
