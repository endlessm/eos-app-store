from add_shortcuts_model import AddShortcutsModel
from osapps.app_shortcut import AppShortcut
from osapps.desktop_locale_datastore import DesktopLocaleDatastore

class AddShortcutsPresenter():
    def __init__(self):
        self._model = AddShortcutsModel()
        self._app_desktop_datastore = DesktopLocaleDatastore()

    def get_category_data(self):
        return self._model.get_category_data()
    
    def create_directory(self, dir_name, image_file, presenter):
        shortcuts = presenter._model._app_desktop_datastore.get_all_shortcuts()
        dir_name = self.check_dir_name(dir_name, shortcuts)
        path = self._model.create_directory(dir_name)
        if path:
            shortcut = AppShortcut(key='', name=dir_name, icon={'normal':image_file})
            presenter._model._app_desktop_datastore.add_shortcut(shortcut)
    
    def get_folder_icons(self, path, hint):
        return self._model.get_folder_icons(path, hint)
    
    def check_dir_name(self, dir_name, shortcuts):
        index = 0
        done = False
        new_name = dir_name
        
        while not done:
            done = True
            for shortcut in shortcuts:
                if shortcut.name() == new_name:
                    index += 1
                    new_name = dir_name + ' ' + str(index)
                    done = False
        
        return new_name
