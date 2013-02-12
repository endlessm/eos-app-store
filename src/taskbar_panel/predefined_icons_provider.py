from gtk import gdk
from desktop_files.desktop_file_utilities import DesktopFileUtilities
from application_store.application_store_model import ApplicationStoreModel

# Create a mapping from application key to minimized icon
# TODO Consider loading models once to serve both app store and task bar
# (currently, the app store re-loads the models every time it is run)
class PredefinedIconsProvider():
    def __init__(self, gdk_helper = gdk, desktop_file_utils = DesktopFileUtilities()):
        self._gdk_helper = gdk_helper

        self._mini_icon_paths = {}
        self._mini_icons = {}

        file_models = desktop_file_utils.get_desktop_file_models(ApplicationStoreModel.DEFAULT_APP_STORE_DIRECTORY)
        for file_model in file_models:
            application_key = file_model.class_name().lower()
            icon_path = file_model.mini_icon()
            self._mini_icon_paths[application_key] = icon_path

    def get_icon_for(self, app_key):
        if app_key not in self._mini_icon_paths:
            return None

        if app_key not in self._mini_icons:
            self._create_icon(app_key)

        return self._mini_icons[app_key]

    def _create_icon(self, app_key):
        icon_path = self._mini_icon_paths[app_key]
        icon_pixbuf = self._gdk_helper.pixbuf_new_from_file(icon_path)
        self._mini_icons[app_key] = icon_pixbuf

