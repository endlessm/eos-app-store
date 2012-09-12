import gtk

class BackgroundChooser(gtk.FileChooserDialog):
    def __init__(self, desktop_view):
        super(BackgroundChooser, self).__init__()
        self._desktop_view = desktop_view

        my_filter = gtk.FileFilter()
        my_filter.add_mime_type('image/png')
        my_filter.add_mime_type('image/jpeg')
        my_filter.add_mime_type('image/gif')
        my_filter.add_mime_type('image/bmp')
        self.add_filter(my_filter)

        self.set_size_request(500, 300)
        self.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)

        button_container = gtk.HBox()
        confirm_button = gtk.Button("Ok")
        confirm_button.connect("button-release-event", self.set_background_callback)

        cancel_button = gtk.Button("Cancel")
        cancel_button.connect("button-release-event", lambda w,e: self.destroy())

        button_container.add(confirm_button)
        button_container.add(cancel_button)
        self.set_extra_widget(button_container)
        
        self.show_all()

    def set_background_callback(self, widget, event):
        try:
            self._desktop_view._set_background(self.get_filename())
            self.destroy()
        except:
            self.warn_user()

    def warn_user(self):
        warning_window = gtk.Dialog("Incorrect File Type", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_REJECT))
        warning_window.set_size_request(275, 150)
        warning_window.connect('response', lambda r, d: warning_window.destroy())

        warning_text = gtk.Label("Please choose a valid image file.")
        warning_text.set_alignment(0.5, 0.3)

        warning_window.vbox.pack_start(warning_text)
        warning_text.show()

        warning_window.run()

