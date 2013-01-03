from all_settings_view import AllSettingsView
from all_settings_model import AllSettingsModel
from background_chooser_launcher import BackgroundChooserLauncher

class AllSettingsPresenter():
    def __init__(self, view, model, backgroundChooserLauncher=BackgroundChooserLauncher()):
        view.add_listener(AllSettingsView.DESKTOP_BACKGROUND, 
                lambda: self._desktop_background(view, model, backgroundChooserLauncher))
        view.add_listener(AllSettingsView.UPDATE_SOFTWARE, 
                lambda: self._update_software(view, model))
        view.add_listener(AllSettingsView.SETTINGS, 
                lambda: self._open_settings(view, model))
        view.add_listener(AllSettingsView.LOGOUT, lambda: self._logout(view, model))
        view.add_listener(AllSettingsView.RESTART, lambda: self._restart(view, model))
        view.add_listener(AllSettingsView.SHUTDOWN, lambda: self._shutdown(view, model))
        view.add_listener(AllSettingsView.FOCUS_OUT, lambda: self.focus_out())
        
        model.add_listener(AllSettingsModel.UPDATE_LOCK, lambda: self._modify_update_button(view, model))
        model.add_listener(AllSettingsModel.UPDATE_STARTED, lambda: self._inform_user_of_update(view, model))
  
        self._model = model
        self._view = view
        self._focus_out_enabled = True
        
        self._modify_update_button(view, model)
        
        view.set_current_version(model.get_current_version())
        
    def focus_out(self):
        if self.is_focus_out_enabled():
            self._view.hide_window()

    def enable_focus_out(self):
        self._focus_out_enabled = True
        
    def disable_focus_out(self):
        self._focus_out_enabled = False
        
    def is_focus_out_enabled(self):
        return self._focus_out_enabled

    def toggle_display(self):
        if self._view.is_displayed():
            self._view.hide_window()
        else:
            self._view.display()
        
    def _modify_update_button(self, view, model):
        if model.can_update():
            view.enable_update_button()
        else:
            view.disable_update_button()

    def _update_software(self, view, model):
        view.hide_window()
        model.update_software()

    def _inform_user_of_update(self, view, model):
        view.inform_user_of_update()

    def _open_settings(self, view, model):
        view.hide_window()
        model.open_settings()
        
    def _desktop_background(self, view, model, backgroundChooserLauncher):
        view.hide_window()
        backgroundChooserLauncher.launch(view)
        
    def _logout(self, view, model):
        view.hide_window()
        if view.confirm(AllSettingsView.LOGOUT_MESSAGE):
            model.logout()
        
    def _restart(self, view, model):
        view.hide_window()
        if view.confirm(AllSettingsView.RESTART_MESSAGE):
            model.restart()
        
    def _shutdown(self, view, model):
        view.hide_window()
        if view.confirm(AllSettingsView.SHUTDOWN_MESSAGE):
            model.shutdown()
