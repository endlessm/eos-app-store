class DesktopPresenter(object):
    def __init__(self, view, model):
        self._model = model
        self._view = view
        self._view.set_presenter(self)
        self._view.set_background_pixbuf(self._model.get_background_pixbuf())
        
        self._is_refreshing = False
        
        self.refresh_view()

    def activate_item(self, app_key, params):
        self._view.hide_folder_window()
        self._model.execute_app(app_key, params)
        
    def move_item(self, shortcuts):
        self._model.set_shortcuts_by_name(shortcuts)
        self._view.refresh(self._model.get_shortcuts(force=True))
    
    def relocate_item(self, sc_moved, sc_folder):
        source_path = '/%s' % sc_moved
        destination_path = '/%s/' % (sc_folder)
        destination_shortchut = self._model.relocate_shortcut(
            source_path, 
            destination_path
            )
        if destination_shortchut is not None:
            self._view.hide_folder_window()
            self._view.show_folder_window(destination_shortchut)
            self._view.refresh(self._model.get_shortcuts(force=True))
            return True
        return False
    
    def refresh_view(self):
        if not self._is_refreshing:
            self._is_refreshing = True
            self._view.refresh(self._model.get_shortcuts())
            self._is_refreshing = False
    
    def submit_feedback(self, message, bug):
        self._model.submit_feedback(message, bug)
        
    def launch_search(self, search_string):
        self._model.launch_search(search_string)
    
    def change_background(self, filename):
        self._model.set_background(filename)
        self._view.set_background_pixbuf(self._model.get_background_pixbuf())
    
    def revert_background(self):
        self.change_background(self._model.get_default_background())
        
    def get_preferences(self):
        return self._model.get_preferences()

    
