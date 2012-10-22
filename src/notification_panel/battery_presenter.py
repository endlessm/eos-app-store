from battery_view import BatteryView
import gobject

class BatteryPresenter():
    REFRESH_TIME = 2000
    
    def __init__(self, view, model, gobj = gobject):
        self._view = view
        self._model = model
        self._gobj = gobj

    def post_init(self):        
        self._view.add_listener(BatteryView.POWER_SETTINGS, 
                lambda: self._open_settings(self._view, self._model))
        self._view.display_battery(self._model.level(), self._model.time_to_depletion(), self._model.charging())
        self._start_poll_battery()
        
    def _start_poll_battery(self):
        self._gobj.timeout_add(self.REFRESH_TIME, self._poll_for_battery)
    
    def _poll_for_battery(self):
        self._view.display_battery(self._model.level(), self._model.time_to_depletion(), self._model.charging())
        return True
            
    def _open_settings(self):
        self._view.hide_window()
        self._model.open_settings()
    
    def display_menu(self):
        self._view.display_menu(self._model.level(), self._model.time_to_depletion())


    