from desktop_layout import DesktopLayout
import gettext

import gtk
import gobject
from gtk import gdk

from shortcut.application_shortcut import ApplicationShortcut
from shortcut.folder_shortcut import FolderShortcut
from shortcut.separator_shortcut import SeparatorShortcut
from shortcut.add_remove_shortcut import AddRemoveShortcut
from folder.folder_window import OpenFolderWindow
from folder.folder_window import FULL_FOLDER_ITEMS_COUNT
from taskbar_panel.taskbar_panel import TaskbarPanel
from add_shortcuts_module.add_shortcuts_view import AddShortcutsView
from eos_util.image import Image
from shortcut.desktop_shortcut import DesktopShortcut
from desktop_page.desktop_page_view import DesktopPageView
from search.search_box import SearchBox
from desktop.base_desktop import BaseDesktop
from desktop_nav_button import DesktopNavButton
from ui.padding_widget import PaddingWidget
from desktop_page.button import Button

gettext.install('endless_desktop', '/usr/share/locale', unicode=True, names=['ngettext'])
gtk.gdk.threads_init()

class EndlessDesktopView(gtk.Window, object):
    _app_shortcuts = {}

    def __init__(self):
        gtk.Window.__init__(self)
        
        width, height = self._get_net_work_area()
        self.resize(width, height)

        self.set_app_paintable(True)
        self.set_can_focus(False)
        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DESKTOP) #@UndefinedVariable
        self.set_decorated(False)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.connect('button-press-event', self.unfocus_widget)
        self.connect('destroy', lambda w: gtk.main_quit())
        self.connect('delete-event', lambda w, e: True) # Prevents <Alt>F4

        self._max_icons_in_row, self._max_rows_in_page = self._calculate_max_icons()

#        screen = gtk.gdk.Screen() #@UndefinedVariable
#        screen.connect('size-changed', lambda s: return) # TODO refresh background and screen content

        self._set_up_desktop(width)

    def _set_up_desktop(self, width):
        self._desktop_page = None

        self._taskbar_panel = TaskbarPanel(self, width)
        taskbar_alignment = PaddingWidget(0.5, 0.5, 1.0, 1.0)
        taskbar_alignment.add(self._taskbar_panel)

        self.desktop_container = gtk.HBox(False, spacing=0)

        self._main_content = PaddingWidget(1.0, 0.5, 1.0, 0.0)
        self._main_content.add(self.desktop_container)

        self.left_page_button = DesktopNavButton('left', lambda w:self._presenter.previous_desktop())
        self.right_page_button = DesktopNavButton('right', lambda w:self._presenter.next_desktop())

        self.desktop_container.pack_start(self.left_page_button, expand=False, fill=False, padding=0)
        self.desktop_container.pack_end(self.right_page_button, expand=False, fill=False, padding=0)

        self.icons_alignment = PaddingWidget(0.5, 0.5, 0.0, 0.0)
        self.desktop_container.pack_start(self.icons_alignment, expand=True, fill=True, padding=0)

        self._base_desktop = BaseDesktop()
        self._base_desktop.set_taskbar_widget(taskbar_alignment)        
        self._base_desktop.set_page_buttons_widget(PaddingWidget(0.5, 0.5, 1.0, 0.0))
        self._base_desktop.set_searchbar_widget(self._create_searchbar())        
        self._base_desktop.set_main_content_widget(self._main_content)       

        self.add(self._base_desktop)
        self.show_all()

    def refresh(self, shortcuts, page_number=0, pages=1, force=False):
        show_page_buttons = pages > 1
        self.left_page_button.set_is_visible(show_page_buttons)
        self.right_page_button.set_is_visible(show_page_buttons)

        if self._desktop_page:
            DesktopShortcut._clear_callbacks()
            self.icons_alignment.remove(self._desktop_page)
            self._desktop_page.destroy()

        self._desktop_page = DesktopPageView(shortcuts, self._max_icons_in_row, self._create_row)
        self.icons_alignment.add(self._desktop_page)

        self._desktop_page.show()
        self.queue_draw()

        self._update_bottom_page_buttons(self._base_desktop.get_page_buttons_widget(), page_number, pages, show_page_buttons)

        self._base_desktop.recalculate_padding(self.desktop_container)

    def _create_searchbar(self):
        searchbox_holder = PaddingWidget(0.5, 0.0, 0, 1.0)
        searchbox = SearchBox()
        searchbox_holder.add(searchbox)

        return searchbox_holder

    def unfocus_widget(self, widget, event):
        widget.set_focus(None)
        self.close_folder_window()
        self._taskbar_panel.close_settings_plugin_window()

    def set_presenter(self, presenter):
        self._presenter = presenter

    def get_presenter(self):
        return self._presenter

    def set_background_image(self, image):
        width, height = self._get_net_work_area()
        image.scale_to_best_fit(width, height)
        
        pixmap = image.pixbuf.render_pixmap_and_mask()[0]
        self.window.set_back_pixmap(pixmap, False)

        self.window.invalidate_rect((0, 0, width, height), False)

    def _update_bottom_page_buttons(self, parent_container, page_number, pages, show_page_buttons):
        if hasattr(self,'_page_buttons_wrapper'):
            parent_container.remove(self._page_buttons_wrapper)
            self._page_buttons_wrapper.destroy()
        page_buttons_holder = gtk.HBox(spacing=7)
        self._page_buttons_wrapper = PaddingWidget(0.5, 0.5, 0.0, 0.0)
        self._page_buttons_wrapper.set_size_request(0, 39)
        self._page_buttons_wrapper.add(page_buttons_holder)
        self._page_buttons_wrapper.show()
        
        page_buttons = []
        
        for page_num in range(0, pages): 
            btn = Button(
                normal=(Image.from_name("button_mini_desktop_normal.png"), ), 
                hover=(Image.from_name("button_mini_desktop__hover_active.png"), ), 
                down=(Image.from_name("button_mini_desktop_down.png"), ), 
                select=(Image.from_name("button_mini_desktop__active.png"), ), 
                invisible=not show_page_buttons)
            page_buttons.append(btn)

            def create_callback(index):
                    return lambda w: self.desktop_page_navigate(index)
            btn.connect("clicked", create_callback(page_num))

            btn.set_size_request(21, 13)
            page_buttons_holder.pack_start(btn, expand=False, fill=False, padding=0)
        
        for button in page_buttons:
            button.unselected()
        
        page_buttons[page_number - 1].selected()
        parent_container.add(self._page_buttons_wrapper)
        page_buttons_holder.show_all()
        
    def desktop_page_navigate(self, index):
        self._presenter.desktop_page_navigate(index + 1)

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

