import sys
from eos_util import image_util

class EndlessDesktopModel(object):
    def __init__(self, app_desktop_datastore, preferences_provider, app_datastore, app_launcher, feedback_manager, time_provider):
        self._app_launcher = app_launcher
        self._feedback_manager = feedback_manager
        self._time_provider = time_provider
        self._app_desktop_datastore = app_desktop_datastore
        self._app_datastore = app_datastore
        self._preferences_provider = preferences_provider

    def get_shortcuts(self):
        return self._app_desktop_datastore.get_all_shortcuts()

    def set_shortcuts(self, shortcuts):
        self._app_desktop_datastore.set_all_shortcuts(shortcuts)

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

    def delete_shortcut(self, shortcut):
        all_shortcuts = [item.name() for item in self._app_desktop_datastore.get_all_shortcuts()]
        for item in all_shortcuts:
            if item == shortcut:
                try:
                    all_shortcuts.remove(item)
                    self._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
                    return True
                except:
                    print >> sys.stderr, "delete shortcut failed!"
                break
        return False
