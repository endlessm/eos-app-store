import transparent_window
from gi.repository import Gtk
from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore

# This type of transparent window extracts the background from the
# underlying desktop background, ignoring any decorations
# such as the taskbar or shortcut icons

class DesktopTransparentWindow():
    
    def __init__(self, parent, location=(0,0), size=None, gradient_type=None,
                 desktop_preference_class = DesktopPreferencesDatastore):
        desktop_preferences = desktop_preference_class.get_instance()
        
        parent_size = parent.get_size()
        width, height = parent_size
        background = None 
        
        # Use the full scaled background image rather than making a copy and cropping it
        super(DesktopTransparentWindow, self).__init__(parent, background, (0, 0), parent_size, gradient_type)
        
        # Now set the location and size of the window within the background
        self.set_location(location)
        self.set_size(size or parent_size)
