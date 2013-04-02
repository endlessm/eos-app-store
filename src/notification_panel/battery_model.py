import gobject
from battery_provider import BatteryProvider
from osapps.app_launcher import AppLauncher
from eos_widgets.abstract_notifier import AbstractNotifier

class BatteryModel(AbstractNotifier):
    SETTINGS_COMMAND = "gksudo gnome-control-center power"
    BATTERY_STATE_CHANGED = 'battery-state-changed'
    
    def __init__(self, battery_provider=BatteryProvider(), _app_launcher = AppLauncher(), gobj=gobject):
        self._battery_provider = battery_provider
        self._app_launcher = _app_launcher
        
        battery_provider.add_battery_callback(self._battery_state_changed)
        
    def open_settings(self):
        self._app_launcher.launch(self.SETTINGS_COMMAND)
    
    def level(self):
        return self._battery.level()
    
    def charging(self):
        return self._battery.charging()
    
    def time_to_depletion(self):
        remaining = self._battery.time_to_depletion()
        time_to_depletion_str = ''
        if remaining:
            minutes = divmod(remaining, 60)[0]
            hours, minutes = divmod(minutes, 60)
            time_to_depletion_str ='%d:%02d' % (hours, minutes)
        return time_to_depletion_str
    
    def _battery_state_changed(self, battery):
        self._battery = battery
        self._notify(self.BATTERY_STATE_CHANGED)

