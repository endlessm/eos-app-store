from add_shortcuts_model import AddShortcutsModel
from osapps.app_shortcut import AppShortcut
from osapps.desktop_locale_datastore import DesktopLocaleDatastore

class AddShortcutsPresenter():
    def __init__(self):
        self._model = AddShortcutsModel()
        self._app_desktop_datastore = DesktopLocaleDatastore()

    def get_category_data(self):
        return self._model.get_category_data()
    
    def create_directory(self, dir_name, image_file):
        return self._model.create_directory(dir_name)
    
    def get_folder_icons(self, path, hint):
        return self._model.get_folder_icons(path, hint)
