from battery_view import BatteryView
import gobject

class BatteryPresenter():
    REFRESH_TIME = 5000
    
    def __init__(self, view, model, gobj=gobject):
        view.add_listener(BatteryView.POWER_SETTINGS, 
                lambda: self._open_settings(view, model))
        self._view = view
        self._model = model
        
        self._view.set_battery(self._model.get_battery())
        self._view.display_battery()
        self._start_poll_battery()
        
    def _start_poll_battery(self):
        gobject.timeout_add(self.REFRESH_TIME, self._poll_for_battery)
    
    def _poll_for_battery(self):
        print "polling..."
        self._view.set_battery(self._model.get_battery())
        self._view.display_battery()
        return True
            
    def _open_settings(self):
        self._view.hide_window()
        self._model.open_settings()


    