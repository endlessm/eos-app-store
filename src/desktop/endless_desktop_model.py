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
    
    def _relocate_shortcut_to_root(self, source_shortcut):
        source_parent = source_shortcut.parent()
        source_parent.remove_child(source_shortcut)
        
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        all_shortcuts.append(source_shortcut)
        self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
        return True
        
    def _relocate_shortcut_to_folder(self, source_shortcut, folder_shortcut):
        source_parent = source_shortcut.parent()
        all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()
        
        if (source_parent is None) and (source_shortcut in all_shortcuts):
            all_shortcuts.remove(source_shortcut)
            folder_shortcut.add_child(source_shortcut)
            self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
            return True
        elif source_parent is not None:
            source_parent.remove_child(source_shortcut)
            folder_shortcut.add_child(source_shortcut)
            self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
            return True
        else:
            print >> sys.stderr, "unknown shortcut location"
        return False
    
    def relocate_shortcut(self, source_shortcut, folder_shortcut):
        if source_shortcut is not None:
            source_parent = source_shortcut.parent()
            all_shortcuts = self._app_desktop_datastore.get_all_shortcuts()

            if folder_shortcut is None:
                if source_parent is not None:
                    return self._relocate_shortcut_to_root(source_shortcut)
            else:
                return self._relocate_shortcut_to_folder(
                    source_shortcut, 
                    folder_shortcut
                    )                
        return False
    
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
