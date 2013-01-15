import gtk
from desktop.desktop_layout import DesktopLayout
from desktop.list_paginator import ListPaginator
from osapps.app_shortcut import AppShortcut

class DesktopPageView(gtk.VBox):

    def __init__(self, shortcuts, columns, create_row_callback):
        super(DesktopPageView, self).__init__(homogeneous=True)
        self.set_spacing(DesktopLayout.VERTICAL_SPACING)        

        self.create_row_callback = create_row_callback

        rowinator = ListPaginator(shortcuts+[AppShortcut("ADD_REMOVE_SHORTCUT_PLACEHOLDER","","")], columns)
        
        for page_num in range(0, rowinator.number_of_pages()):
            row = self.create_row_callback(rowinator.current_page(), rowinator.is_last_page())
            self.pack_start(row, expand=False, fill=False, padding=0)
            rowinator.next()
        

            


       


            
            
            