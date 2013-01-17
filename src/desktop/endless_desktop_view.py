from desktop_layout import DesktopLayout
import sys
import gettext

import gtk
import gobject
from gtk import gdk

from shortcut.application_shortcut import ApplicationShortcut
from shortcut.folder_shortcut import FolderShortcut
from shortcut.separator_shortcut import SeparatorShortcut
from shortcut.add_remove_shortcut import AddRemoveShortcut
from desktop_page.desktop_page import DesktopPage
from folder.folder_window import OpenFolderWindow
from folder.folder_window import FULL_FOLDER_ITEMS_COUNT
from notification_panel.notification_panel import NotificationPanel
from taskbar_panel.taskbar_panel import TaskbarPanel
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView
from eos_util.image import Image
from shortcut.desktop_shortcut import DesktopShortcut
from desktop.list_paginator import ListPaginator
from desktop_page.desktop_page_view import DesktopPageView
from desktop_page.responsive import Button


gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window):
    
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
        self.set_app_paintable(True)

        # -----------WORKSPACE-----------

        self._align = gtk.Alignment(1.0, 1.0, 1.0, 1.0)

        self._taskbar_panel = TaskbarPanel(self, width)

        self._notification_panel = NotificationPanel(self)

        taskbar_alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        taskbar_alignment.add(self._taskbar_panel)

        # Main window layout
        self._desktop = gtk.VBox(False, 2)
        self._desktop.pack_start(self._notification_panel, False, False, 0)

        self._desktop.pack_start(self._align, True, True, 0)
        self._desktop.pack_end(taskbar_alignment, False, False, 0)

        self.add(self._desktop)
        self.show_all()

        self._max_icons_in_row, self._max_rows_in_page = self._calculate_max_icons()

        screen = gtk.gdk.Screen() #@UndefinedVariable
        screen.connect('size-changed', lambda s: self._set_background(self.BACKGROUND_NAME))

    def unfocus_widget(self, widget, event):
        widget.set_focus(None)
        self.close_folder_window()
        self._notification_panel.close_settings_plugin_window()

    def set_presenter(self, presenter):
        self._presenter = presenter

    def get_presenter(self):
        return self._presenter

    def set_background_image(self, image):
        width, height = self._get_net_work_area()
        image.scale_to_best_fit(width, height)
        
        pixmap, mask = image.pixbuf.render_pixmap_and_mask()

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

    def _resize_background(self, screen_width, screen_height, pixbuf):
        image = Image(pixbuf)
        image.scale_to_best_fit(screen_width, screen_height)
        return image.pixbuf
    
    #TODO: this fixes one symptom of performance and memory leaks by cleaning up callbacks, please refactor
    def clean_up_legacy_page(self):
        child = self._align.get_child()
        if child:
            child.parent.remove(child)
            child.destroy()
            del child
        
        DesktopShortcut._clear_callbacks()


    def are_page_buttons_disabled(self, pages):
        return not pages > 1

    def set_up_base_desktop(self):
        self.desktop_vbox = gtk.VBox()
        self.top_vbox = gtk.VBox()
        self.top_vbox.set_size_request(0, 39)
        self.desk_container = gtk.HBox(homogeneous=False, spacing=0)
        self.desk_container_wraper = gtk.Alignment(1.0, 0.5, 1.0, 0.0)
        self.desk_container_wraper.add(self.desk_container)
        self.icons_alignment = gtk.Alignment(0.5, 0.5, 0.0, 0.0)

    def setup_left_right_page_buttons(self, hide_page_buttons):
        self.prev_button = Button(
            normal=(), 
            hover=(Image.from_name("button_arrow_desktop_left_hover.png"), ), 
            down=(Image.from_name("button_arrow_desktop_left_down.png"), ), 
            invisible=hide_page_buttons)
        self.prev_button.connect("clicked", lambda w:self._presenter.previous_desktop())
        self.prev_button.set_size_request(50, 420)
        self.prev_button_wrap = Button.align_it(self.prev_button)
        self.next_button = Button(
            normal=(), 
            hover=(Image.from_name("button_arrow_desktop_right_hover.png"), ), 
            down=(Image.from_name("button_arrow_desktop_right_down.png"), ), 
            invisible=hide_page_buttons)
        self.next_button.connect("clicked", lambda w:self._presenter.next_desktop())
        self.next_button.set_size_request(50, 420)
        self.next_button_wrap = Button.align_it(self.next_button)

    def add_widgets_to_desktop(self, shortcuts):
        self.desk_container.pack_start(self.prev_button_wrap, expand=False, fill=False, padding=0)
        desktop_page = DesktopPageView(shortcuts, self._max_icons_in_row, self._create_row)
        self.icons_alignment.add(desktop_page)
        self.desk_container.pack_start(self.icons_alignment, expand=True, fill=True, padding=0)
        self.desk_container.pack_end(self.next_button_wrap, expand=False, fill=False, padding=0)
        self.desktop_vbox.pack_start(self.top_vbox, expand=False, fill=False, padding=0)
        self.desktop_vbox.pack_start(self.desk_container_wraper, expand=True, fill=True, padding=0)
        self.desktop_vbox.show_all()

    def setup_bottom_page_buttons(self, index, pages, hide_page_buttons):
        self.bottom_hbox = gtk.HBox(spacing=7)
        wrapper = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        wrapper.set_size_request(0, 39)
        wrapper.add(self.bottom_hbox)
        wrapper.show()
        self._page_buttons = []
        for page_num in range(0, pages):
            btn = Button(
                normal=(Image.from_name("button_mini_desktop_normal.png"), ), 
                hover=(Image.from_name("button_mini_desktop__hover_active.png"), ), 
                down=(Image.from_name("button_mini_desktop_down.png"), ), 
                select=(Image.from_name("button_mini_desktop__active.png"), ), 
                invisible=hide_page_buttons)
            self._page_buttons.append(btn)
            btn.connect("clicked", self.desktop_page_navigate)
            #btn.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,0,0))
            btn.set_size_request(21, 13)
            self.bottom_hbox.pack_start(btn, expand=False, fill=False, padding=0)
        
        for button in self._page_buttons:
            button.unselected()
        
        self._page_buttons[index].selected()
        self.desktop_vbox.pack_end(wrapper, expand=False, fill=False, padding=0)
        self.bottom_hbox.show_all()

    def align_and_display_desktop(self):
        self.desktop_vbox.show()
        self._align.add(self.desktop_vbox)
        self.desktop_vbox.show()
        self._align.show()

    def refresh(self, shortcuts, index=0, pages=1, force=False):
        self.clean_up_legacy_page()
        hide_page_buttons = self.are_page_buttons_disabled(pages)
        self.set_up_base_desktop()
        self.setup_left_right_page_buttons(hide_page_buttons)
        self.add_widgets_to_desktop(shortcuts)
        self.setup_bottom_page_buttons(index, pages, hide_page_buttons)
        self.align_and_display_desktop()
        
    def desktop_page_navigate(self, widget):
        index = self._page_buttons.index(widget)
        self._presenter.desktop_page_navigate(index)

    def _add_icon_clicked_callback(self, widget, event):
        self.popup.show_all()
        self.popup.popup(None, None, None, event.button, event.time)

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


    def _create_folder_shortcut(self, shortcut, row):
        item = FolderShortcut(shortcut, self._folder_icon_clicked_callback)
        item.connect("folder-shortcut-activate", self._folder_icon_clicked_callback)
        item.connect("folder-shortcut-relocation", self._relocation_callback)
        item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
        item.connect("desktop-shortcut-rename", self._rename_callback)
        item.show()
        row.pack_start(item, False, False, 0)
        return item


    def _create_add_remove_shortcut(self, row):
        item = AddRemoveShortcut(callback=self.show_add_dialogue)
        item.connect("application-shortcut-remove", self._delete_shortcuts)
        item.show()
        row.pack_start(item, False, False, 0)
        return item

    def _create_application_shortcut(self, shortcut, row):
        item = ApplicationShortcut(shortcut)
        item.connect("application-shortcut-rename", lambda w, shortcut, new_name:self._presenter.rename_item(shortcut, new_name))
        item.connect("application-shortcut-activate", lambda w, app_key, params:self._presenter.activate_item(app_key, params))
        item.connect("desktop-shortcut-dnd-begin", self._dnd_begin)
        item.connect("desktop-shortcut-rename", self._rename_callback)
        item.show()
        row.pack_start(item, False, False, 0)
        return item


    def _adjust_separator(self, row, sep_last, item):
        sep_new = SeparatorShortcut(width=DesktopLayout.get_separator_width(), height=DesktopLayout.ICON_HEIGHT)
        sep_new.connect("application-shortcut-move", self._rearrange_shortcuts)
        row.pack_start(sep_new, False, False, 0)
        sep_last.set_right_separator(sep_new)
        sep_last.set_right_widget(item)
        sep_new.set_left_separator(sep_last)
        sep_new.set_left_widget(item)
        sep_last = sep_new
        return sep_new, sep_last

    def _create_row(self, items, last_row=False):
        
        row = gtk.HBox()
        row.show()

        sep_last = SeparatorShortcut(width=DesktopLayout.get_separator_width(), height=DesktopLayout.ICON_HEIGHT)
        sep_last.connect("application-shortcut-move", self._rearrange_shortcuts)
        row.pack_start(sep_last, False, False, 0)

        for shortcut in items:
            if shortcut.has_children():
                item = self._create_folder_shortcut(shortcut, row)
                sep_new, sep_last = self._adjust_separator(row, sep_last, item)
            elif shortcut.key() == "ADD_REMOVE_SHORTCUT_PLACEHOLDER":
                item = self._create_add_remove_shortcut(row)
            else:
                item = self._create_application_shortcut(shortcut, row)
                sep_new, sep_last = self._adjust_separator(row, sep_last, item)

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
        # For now, these are hard-coded constants.
        # TODO: Calculate based on available desktop size (scale with display resolution)
        return (DesktopLayout.MAX_ICONS_IN_ROW, DesktopLayout.MAX_ROWS_OF_ICONS)

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
        add_shortcut_popup = AddShortcutsView(parent=self)
        add_shortcut_popup.show()

    def _delete_shortcuts(self, widget, sc_deleted):
        self._presenter.delete_shortcut(sc_deleted)
    
    def _rename_callback(self, widget, new_name):
        changed_shortcut = self._presenter.rename_shortcut(widget.get_shortcut(), new_name)
        widget.set_shortcut(changed_shortcut)
        widget._label_event_box.refresh()

