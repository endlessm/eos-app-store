from all_settings_view import AllSettingsView
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

        view.set_current_version(model.get_current_version())
        view.display()

    def _update_software(self, view, model):
        view.hide_window()
        if view.confirm(AllSettingsView.UPDATE_MESSAGE):
            model.update_software()

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
