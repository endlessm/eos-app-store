import gtk
from ui.glade_ui_elements import *

class UiUtils():
    _elements = {'bugs_and_feedback': bugs_and_feedback}
    
    def get_builder_for_file(self, filename):
        builder = gtk.Builder()
        builder.set_translation_domain('endless_desktop')        
        try: 
            builder.add_from_file("../ui/" + filename + ".glade")
        except:
            builder.add_from_string(self._elements[filename])
            
        return builder

