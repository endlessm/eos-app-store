from battery_view import BatteryView
from battery_model import BatteryModel
import gobject

class BatteryPresenter():
    def __init__(self, view, model, gobj = gobject):
        self._view = view
        self._model = model
        self._gobj = gobj

    def post_init(self):
        self._view.add_listener(BatteryView.POWER_SETTINGS, 
            lambda: self._open_settings())
        self._model.add_listener(BatteryModel.BATTERY_STATE_CHANGED, 
            lambda: self._update_battery_state())
    
        self._update_battery_state()
        
    def _update_battery_state(self):
        self._view.display_battery(self._model.level(), self._model.time_to_depletion(), self._model.charging())
            
    def _open_settings(self):
        self._view.hide_window()
        self._model.open_settings()
    
    def display_menu(self):
        self._view.display_menu(self._model.level(), self._model.time_to_depletion())
    