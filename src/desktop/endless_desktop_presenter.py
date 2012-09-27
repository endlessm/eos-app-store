from desktop.endless_desktop_model import EndlessDesktopModel
import sys

class DesktopPresenter(object):
    def __init__(self, view, model=EndlessDesktopModel()):
        self._model = model
        self._view = view
        self._view.set_presenter(self)
        
        self._is_refreshing = False
        
        self.refresh_view()

    def activate_item(self, app_key, params):
        self._view.hide_folder_window()
        self._model.execute_app(app_key, params)
        
    def move_item(self, shorcuts):
        print 'TODO: permanently store shortcuts order', shorcuts
    
    def refresh_view(self):
        if not self._is_refreshing:
            self._is_refreshing = True
            self._view.refresh(self._model.get_shortcuts())
            self._is_refreshing = False
    
    def submit_feedback(self, message, bug):
        self._model.submit_feedback(message, bug)
        
    def launch_search(self, search_string):
        self._model.launch_search(search_string)
