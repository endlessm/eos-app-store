import gobject
from battery_provider import BatteryProvider
from osapps.app_launcher import AppLauncher

class BatteryModel():
    
    SETTINGS_COMMAND = "gksudo gnome-control-center power"
    
    def __init__(self, gobj=gobject):
#        self._start_battery_polling()
        self._app_launcher = AppLauncher()
        
    def get_battery(self):
        return BatteryProvider.get_battery()
        
    def _start_battery_polling(self):
        gobject.timeout_add(self.REFRESH_TIME, self._poll_for_battery)
    
    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)
    
    def _level(self):
        return BatteryProvider.get_battery().level()
    
    def _time_to_depletion(self):
        return BatteryProvider.get_battery().time_to_depletion()    

