class DesktopPresenter(object):
    def __init__(self, view, model):
        self._model = model
        self._view = view
        self._view.set_presenter(self)
        self._view.set_background_pixbuf(self._model.get_background_pixbuf())
        
        self._is_refreshing = False
        
        self.refresh_view()

    def get_shortcut_by_name(self, shortcut_name):
        all_shortcuts = self._model.get_shortcuts()
        for shortcut in all_shortcuts:
            if shortcut_name == shortcut.name():
                return shortcut
        return None
        
    def activate_item(self, app_key, params):
        self._view.hide_folder_window()
        self._model.execute_app(app_key, params)
        
    def move_item(self, shortcuts):
        self._model.set_shortcuts(shortcuts)
        self._view.refresh(self._model.get_shortcuts(force=True), force=True)
        
    def _page_change_callback(self):
        self._view.refresh(self._model.get_shortcuts())
    
    def relocate_item(self, source_shortcut, folder_shortcut):
        self._view.close_folder_window()
        success = self._model.relocate_shortcut(
            source_shortcut, 
            folder_shortcut
            )
        all_shortcuts = self._model.get_shortcuts(force=True)
        self._view.refresh(all_shortcuts, force=True)
        if success:
            if folder_shortcut is not None:
                self._view.show_folder_window_by_name(folder_shortcut.name())
            return True
        return False
        
    def move_item_right(self, source_shortcut, right_shortcut, all_shortcuts):
        if source_shortcut in all_shortcuts:
            all_shortcuts.remove(source_shortcut)
        index = all_shortcuts.index(right_shortcut)
        all_shortcuts.insert(index, source_shortcut)
    
    def move_item_left(self, source_shortcut, left_shortcut, all_shortcuts):
        if source_shortcut in all_shortcuts:
            all_shortcuts.remove(source_shortcut)
        index = all_shortcuts.index(left_shortcut) + 1
        if index < len(all_shortcuts):
            all_shortcuts.insert(index, source_shortcut)
        else:
            all_shortcuts.append(source_shortcut)
        
    def rearrange_shortcuts(self, source_shortcut, left_shortcut, 
            right_shortcut
            ):
            
        all_shortcuts = self._model.get_shortcuts()
        if source_shortcut.parent() is not None:
            self.relocate_item(source_shortcut, None)
            
        if right_shortcut is not None:
            self.move_item_right(source_shortcut, right_shortcut, all_shortcuts)
            self.move_item(all_shortcuts)
        elif left_shortcut is not None:
            self.move_item_left(source_shortcut, left_shortcut, all_shortcuts)
            self.move_item(all_shortcuts)
        else:
            pass
    
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

    def delete_shortcut(self, what):
        self._model.delete_shortcut(what)
        self._view.refresh(self._model.get_shortcuts(force=True))
    
    def rename_shortcut(self, shortcut_obj, new_name):
        all_shortcuts = self._model.get_shortcuts()
        if not shortcut_obj._name == new_name.strip():
            new_name = self.check_shortcut_name(new_name, all_shortcuts)
            shortcut_obj._name = new_name
            self._model._app_desktop_datastore.set_all_shortcuts(all_shortcuts)
        return shortcut_obj
    
    def check_shortcut_name(self, name, shortcuts):
        index = 0
        done = False
        new_name = name
        
        while not done:
            done = True
            for shortcut in shortcuts:
                if shortcut.name() == new_name:
                    index += 1
                    new_name = name + ' ' + str(index)
                    done = False
        
        return new_name
