import gobject
from battery_provider import BatteryProvider
from osapps.app_launcher import AppLauncher
import datetime

class BatteryModel():
    
    SETTINGS_COMMAND = "gksudo gnome-control-center power"
    
    def __init__(self, battery_provider=BatteryProvider(), _app_launcher = AppLauncher(), gobj=gobject):
        self._battery_provider = battery_provider
        self._app_launcher = _app_launcher
        
    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)
    
    def level(self):
        return self._battery_provider.get_battery().level()
    
    def charging(self):
        return self._battery_provider.get_battery().charging()
    
    def time_to_depletion(self):
        remaining = self._battery_provider.get_battery().time_to_depletion()
        time_to_depletion_str = ''
        if remaining:
            m, s = divmod(remaining, 60)
            h, m = divmod(m, 60)
            time_to_depletion_str ='%d:%02d' % (h, m)
        return time_to_depletion_str

