from desktop.endless_desktop_model import EndlessDesktopModel
import sys

class DesktopPresenter(object):
    def __init__(self, view, model=EndlessDesktopModel()):
        self._model = model
        self._view = view
        self._view.set_presenter(self)
        
        self._is_refreshing = False
        
        self.refresh_view()

    def add_item(self, shortcut):
        self._model.add_item(shortcut)
        self.refresh_view()
        
    def remove_item(self, app_id):
        self._model.remove_item(app_id)
        self.refresh_view()

    def rename_item(self, shortcut, new_name):
        self._model.rename_item(shortcut, new_name)
        self.refresh_view()
        
    def move_item(self, indexes):
        self._model.reorder_shortcuts(indexes)
        self.refresh_view()
    
    def activate_item(self, app_id):
        self._view.hide_folder_window()
        self._model.execute_app_with_id(app_id)
    
    def load_children(self, shortcut):
        if shortcut.has_children() and len(shortcut.get_children()) <= 0:
            shortcut = self._model.load_children(shortcut)
        return shortcut
    
    def refresh_view(self):
        if not self._is_refreshing:
            self._is_refreshing = True
            self._view.refresh(self._model.get_shortcuts())
            self._view.populate_popups(self._model.get_menus())
            self._is_refreshing = False
    
    def submit_feedback(self, message, bug):
        self._model.submit_feedback(message, bug)
        
    def launch_search(self, search_string):
        self._model.launch_search(search_string)
