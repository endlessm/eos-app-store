import sys
from util import image_util
from osapps.app_shortcut import AppShortcut

class EndlessDesktopModel(object):
    def __init__(self, app_desktop_datastore, preferences_provider, app_datastore, app_launcher, feedback_manager, time_provider):
        self._app_launcher = app_launcher
        self._feedback_manager = feedback_manager
        self._time_provider = time_provider
        self._app_desktop_datastore = app_desktop_datastore
        self._app_datastore = app_datastore
        self._preferences_provider = preferences_provider

    def get_shortcuts(self, force=False):
        return self._app_desktop_datastore.get_all_shortcuts(force=force)

    def set_shortcuts_by_name(self, shortcuts_names):
        self._app_desktop_datastore.set_all_shortcuts_by_name(shortcuts_names)
    
    def relocate_shortcut(self, source_path, destination_path):
        if (len(destination_path.strip()) == 0) or (len(source_path.strip()) == 0):
            return None
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        sc_cource = None
        sc_destination = None
        for sc in all_shortcuts:
            if sc_cource is None:
                sc_cource = AppShortcut.traverse_path(sc, source_path)
            if sc_destination is None:
                sc_destination = AppShortcut.traverse_path(sc, destination_path)
            if (sc_cource is not None) and (sc_destination is not None):
                break
        if (sc_cource is not None) and (sc_destination is not None):
            sc_destination.add_child(sc_cource)
            all_shortcuts.remove(sc_cource)
            self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
            return sc_destination
        return None
    
    def execute_app(self, app_key, params):
        app = self._app_datastore.get_app_by_key(app_key)

        if app:
            self._app_launcher.launch(app.executable(), params)
        else:
            print >> sys.stderr, "could not find app: "+app_key
        
    def submit_feedback(self, message, bug):
        data = {"message":message, "timestamp":self._time_provider.get_current_time(), "bug":bug}
        self._feedback_manager.write_data(data)

    def launch_search(self, search_string):
        self._app_launcher.launch_browser(search_string)
        
    def set_background(self, filename):
        new_image_path = image_util.image_path(filename)
        self._preferences_provider.set_background(new_image_path)
        
    def get_background_pixbuf(self):
        return self._preferences_provider.get_background_pixbuf()

    def get_default_background(self):
        return self._preferences_provider.get_default_background()
