import gtk
from util import image_util
from util.image_eventbox import ImageEventBox
from responsive import Button

class DesktopPage(gtk.VBox):
        
    pages = []
    page = None
    page_buttons = []
    _current_page_index = 0
    _last_page_index = None
    
    @classmethod
    def calc_pages(
            cls, 
            items, 
            create_row_callback, 
            reload_callback, 
            max_items_in_row=7, 
            max_rows_in_page=4
            ):
        cls.pages = []
        cls.items = items
        cls.create_row_callback = create_row_callback
        cls.reload_callback = reload_callback
        cls.max_items_in_row = max_items_in_row
        cls.max_rows_in_page = max_rows_in_page
        cls.max_items_in_page = (max_items_in_row*max_rows_in_page)-1
        
        pages_count = len(cls.items) / cls.max_items_in_page
        if (len(cls.items) % cls.max_items_in_page) != 0:
            pages_count += 1
        
        cls.pages = []
        for page_index in range(0, pages_count):
            cls.pages.append(page_index*cls.max_items_in_page)
        
    @classmethod
    def get_pages_count(cls):
        return len(cls.pages)
        
    @classmethod
    def get_current_page_index(cls):
        return cls._current_page_index
        
    @classmethod
    def get_current_page(cls):
        cls.page = DesktopPage()
        if cls._current_page_index > (len(cls.pages)-1):
            cls._current_page_index = len(cls.pages)-1
        offset = cls.pages[cls._current_page_index]
        visible_items = cls.items[offset:offset+(cls.max_items_in_page)]
        last_row = False
        rows_count = 0
        while len(visible_items) > 0:
            row = visible_items[:cls.max_items_in_row]
            visible_items = visible_items[len(row):]
            if len(row) < cls.max_items_in_row:
                last_row = True
            row_widget = cls.create_row_callback(row, last_row=last_row)
            row_widget.show()
            cls.page.desk_area.pack_start(
                row_widget, 
                expand=False, 
                fill=False, 
                padding=0
                )
            rows_count += 1
            
            if last_row or (not rows_count < cls.max_rows_in_page):
                break
                
        if len(row) == cls.max_items_in_row:
            row_widget = cls.create_row_callback([], last_row=True)
            row_widget.show()
            cls.page.desk_area.pack_start(
                row_widget, 
                expand=False, 
                fill=False, 
                padding=0
                )
                
        cls.update_images(cls._current_page_index)
        return cls.page
        
    @classmethod
    def has_next(cls):
        if cls._current_page_index < (len(cls.pages)-1):
            return True
        return False
        
    @classmethod
    def has_prev(cls):
        if cls._current_page_index > 0:
            return True
        return False
        
    @classmethod
    def next_page(cls):
        if cls._current_page_index < len(cls.pages)-1:
            cls._current_page_index += 1
            cls.reload_callback()
        cls.update_images(cls._current_page_index)
        
    @classmethod
    def prev_page(cls):
        if cls._current_page_index > 0:
            cls._current_page_index -= 1
            cls.reload_callback()
        cls.update_images(cls._current_page_index)
        
    @classmethod
    def first_page(cls):
        cls._current_page_index = 0
        cls.reload_callback()
        cls.update_images(cls._current_page_index)
        
    @classmethod
    def update_images(cls, index):
        i = 0
        for btn in cls.page_buttons:
            if i == index:
                btn.selected()
            else:
                btn.unselected()
            i += 1
        
    @classmethod
    def goto_page(cls, index):
        if cls._current_page_index != index:
            if (index >= 0) and (index < len(cls.pages)):
                cls._current_page_index = index
                cls.reload_callback()
        cls.update_images(cls._current_page_index)
        
    @classmethod
    def last_page(cls):
        cls._current_page_index = len(cls.pages)-1
        cls.reload_callback()
        cls.update_images(cls._current_page_index)
       
    @classmethod
    def _goto_page_callback(cls, w):
        DesktopPage.goto_page(w.page_index)
        
    def __init__(self):
        super(DesktopPage, self).__init__()
        self.top_vbox = gtk.VBox()
        self.top_vbox.set_size_request(0, 39)
        
        self.desk_container = gtk.HBox(homogeneous=False, spacing=0)
        #self.desk_container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,238,0))
        
        self.desk_container_wraper = gtk.Alignment(1.0, 0.5, 1.0, 0.0)
        #self.desk_container_wraper.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(35,238,0))
        self.desk_container_wraper.add(self.desk_container)
        
        self.bottom_hbox = gtk.HBox(spacing=7)
        
        wraper = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        wraper.set_size_request(0, 39)
        #wraper.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(35,238,0))
        
        wraper.add(self.bottom_hbox)
        wraper.show()

        self.__class__.page_buttons = []
        for i in range(0, DesktopPage.get_pages_count()):
            btn = Button(
                normal = (image_util.image_path("button_mini_desktop_normal.png"),), 
                hover = (image_util.image_path("button_mini_desktop__hover_active.png"),), 
                down = (image_util.image_path("button_mini_desktop_down.png"),),
                select = (image_util.image_path("button_mini_desktop__active.png"),)
                )
            self.__class__.page_buttons.append(btn)
            btn.page_index = i
            btn.connect("clicked", DesktopPage._goto_page_callback)
            #btn.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,0,0))
            btn.set_size_request(21, 13)
            self.bottom_hbox.pack_start(btn, expand=False, fill=False, padding=0)
        self.__class__.update_images(self.__class__.get_current_page_index())
        
        self.icons_alignment = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        
        self.desk_area = gtk.VBox(homogeneous=True)
        self.desk_area.set_spacing(60)
        
        
        hide_btn = True
        if self.__class__.has_prev():
            hide_btn = False
        self.prev_button = Button(
            normal = (), 
            hover = (image_util.image_path("button_arrow_desktop_left_hover.png"),), 
            down = (image_util.image_path("button_arrow_desktop_left_down.png"),), 
            invisible = hide_btn
            )
        self.prev_button.connect("clicked", lambda w: DesktopPage.prev_page())
        self.prev_button.set_size_request(50, 420)
        
        self.prev_button_wrap = Button.align_it(self.prev_button)
        
        hide_btn = True
        if self.__class__.has_next():
            hide_btn = False
        self.next_button = Button(
            normal = (), 
            hover = (image_util.image_path("button_arrow_desktop_right_hover.png"),), 
            down = (image_util.image_path("button_arrow_desktop_right_down.png"),), 
            invisible = hide_btn
            )
        self.next_button.connect("clicked", lambda w: DesktopPage.next_page())
        self.next_button.set_size_request(50, 420)
        self.next_button_wrap = Button.align_it(self.next_button)
        
        self.icons_alignment.add(self.desk_area)
        self.desk_container.pack_start(self.prev_button_wrap, expand=False, fill=False, padding=0)
        self.desk_container.pack_start(self.icons_alignment, expand=True, fill=True, padding=0)
        self.desk_container.pack_end(self.next_button_wrap, expand=False, fill=False, padding=0)
        
        self.pack_start(self.top_vbox, expand=False, fill=False, padding=0)
        self.pack_start(self.desk_container_wraper, expand=True, fill=True, padding=0)
        self.pack_end(wraper, expand=False, fill=False, padding=0)
        
        self.show_all()
        
                
    
    
