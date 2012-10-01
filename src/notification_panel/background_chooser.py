import gtk

class BackgroundChooser(gtk.FileChooserDialog):
    def __init__(self, view):
        super(BackgroundChooser, self).__init__()
        self._desktop_presenter = view._parent.get_toplevel().get_presenter()

        image_filter = gtk.FileFilter()
        image_filter.set_name("Image Files")
        image_filter.add_mime_type('image/*')
        self.add_filter(image_filter)

        all_filter = gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        self.add_filter(all_filter)

        self.set_size_request(500, 300)
        self.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.set_title("Choose background image")

        button_container = gtk.HBox()
        confirm_button = gtk.Button("Ok")
        confirm_button.connect("button-release-event", self.set_background_callback)

        cancel_button = gtk.Button("Cancel")
        cancel_button.connect("button-release-event", lambda w,e: self.destroy())

        revert_background_button = gtk.Button("Default Background")
        revert_background_button.connect("button-release-event", self.revert_background_callback)

        button_container.add(confirm_button)
        button_container.add(revert_background_button)
        button_container.add(cancel_button)
        self.set_extra_widget(button_container)
        
        self.show_all()

    def set_background_callback(self, widget, event):
        try:
            self._desktop_presenter.change_background(self.get_filename())
            self.destroy()
        except RuntimeError as e:
            print repr(e)
            self.warn_user()

    def revert_background_callback(self, widget, event):
        try:
            self._desktop_presenter.revert_background()
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

