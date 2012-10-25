import gtk
import os
from util.image_eventbox import ImageEventBox
from util import image_util

class AddFolderBox(gtk.VBox):
    def __init__(self, parent=None, add_remove_widget=None):
        super(AddFolderBox, self).__init__(self)
        self.set_homogeneous(False)
        self.set_spacing(10)
        self._parent = parent
        #self._add_remove_widget = add_remove_widget
        # first label
        self._label_1 = gtk.Label('\n1. NAME YOUR FOLDER')
        self._label_2 = gtk.Label('2. PICK A SYMBOL')
        #text entry
        self._hbox = gtk.HBox()
        self._text_entry = gtk.Entry(50)
        self._text_entry.set_alignment(0.5)
        self._hbox.pack_start(self._text_entry)
        self._text_entry.set_text('Untitled')
        self.pack_start(self._label_1, True, True, 0)
        self.pack_start(self._hbox, True, False, 0)
        self.pack_start(self._label_2, True, True, 0)
        #@TODO: divider

        # a grid of icons
        
        files = self._get_folder_icons('', 'folder')
        icons = []
        for fi in files:
            #get all needed images
            #images = self.get_images('/usr/share/icons/oxygen/48x48/places/'+fi)
            #create event box
            image_box = ImageEventBox(None)
            image_box.set_size_request(64, 64)
            image_box.set_images(self.get_images('/usr/share/icons/oxygen/48x48/places/'+fi))
            image_box.connect("enter-notify-event", self._display_plus, parent._add_remove_widget)
            image_box.connect("leave-notify-event", self._remove_plus, parent._add_remove_widget)
            image_box.connect("button-release-event", self._create_folder, '/usr/share/icons/oxygen/48x48/places/'+fi)
            image_box.show()
            icons.append(image_box)

        num_of_icons = len(files)
        columns = int(500/82)
        rows = int(num_of_icons/columns) + 1
        self._table = gtk.Table(rows, columns)
        self._table.show()
        col = row = 0
        icons_hbox = gtk.HBox()
        icons_hbox.show()
        for num in range(len(icons)):
            if (num)%columns == 0:
                col = 0
                row = row + 1
            self._table.attach(icons[num], col, col+1, row, row+1, ypadding=25, xpadding=25)
            col = col + 1

        self._table.show()
        self._bottom_center = gtk.Alignment(0.5, 0, 0, 0)
        self._bottom_center.add(self._table)
        self.pack_start(self._bottom_center)
        self.show_all()
        
    def _get_folder_icons(self, path='', hint='folder'):
        if not path:
            path = '/usr/share/icons/oxygen/48x48/places/'
    
        icon_list = os.listdir(path)
    
        for icon in icon_list:
            if not hint in icon:
                icon_list.remove(icon)
        return icon_list
        
#    def set_table(self, table):
#        self._table = table
#        self.show_all()
#    
#    def fill_table(self, images):
#        print 'Should populate table with images'
        
    def get_images(self, image_path):
        return (
            image_util.image_path("endless-shortcut-well.png"),
            #image_util.image_path("endless-shortcut-background.png"),
            image_path,
            image_util.image_path("endless-shortcut-foreground.png")
            )
    
    def _display_plus(self, widget, event, add_remove_widget):
        images_tuple = widget._images
        images_list = list(images_tuple)
        images_list.append(image_util.image_path("delete_ok_active.png"))
        widget.set_images(tuple(images_list))
        widget.hide()
        widget.show()
        add_remove_widget._event_box.set_images(images_tuple)
        add_remove_widget.hide()
        add_remove_widget.show()
    
    def _remove_plus(self, widget, event, add_remove_widget):
        images = list(widget._images)
        widget.set_images(tuple(images[:-1]))
        widget.hide()
        widget.show()
        add_remove_widget._event_box.set_images(add_remove_widget.get_images())
        add_remove_widget.hide()
        add_remove_widget.show()
    
    def _create_folder(self, widget, event, image_file):
        print 'Creating folder...'
        if self._text_entry.get_text() != 'Untitled' and self._text_entry.get_text():
            self._parent.create_folder(self._text_entry.get_text(), image_file)
            self._parent.destroy(None, None)
        else:
            print 'FOLDER MUST HAVE A NAME!'
        print 'Done.'
