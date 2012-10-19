from battery_view import BatteryView

class BatteryPresenter():
    def __init__(self, view, model):
        view.add_listener(BatteryView.POWER_SETTINGS, 
                lambda: self._open_settings(view, model))
#        view.add_listener(BatteryView.POWER_MENU, 
#                lambda: self._open_menu(view, model))
        
#        view.display()
    
    def _open_settings(self, view, model):
        view.hide_window()
        model.open_settings()
        
    def _desktop_background(self, view, model, backgroundChooserLauncher):
        view.hide_window()
        backgroundChooserLauncher.launch(view)

