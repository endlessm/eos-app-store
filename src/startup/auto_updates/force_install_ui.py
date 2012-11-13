import gtk
from ui import glade_ui_elements

class ForceInstallUI():
    def launch_ui(self):
        builder = gtk.Builder()
        builder.add_from_string(glade_ui_elements.force_install)

        window = builder.get_object("dialog-window")
        window.set_wmclass("eos-dialog", "Eos-dialog")
        
        window.show_all()

if __name__ == "__main__":
    ForceInstallUI().launch_ui()
    gtk.main()
