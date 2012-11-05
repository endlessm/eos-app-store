import gtk

from eos_log import log
from util.dbus_utils import DbusUtils

class BatteryProvider():
    AC_ADAPTER_TYPE = 'ac_adapter'
    AC_ADAPTER_PRESENT_PROPERTY = 'ac_adapter.present'

    BATTERY_TYPE = 'battery'
    BATTERY_DISCHARGING_PROPERTY = 'battery.rechargeable.is_discharging'
    BATTERY_PERCENTAGE_PROPERTY = 'battery.charge_level.percentage'
    BATTERY_REMAINING_TIME_PROPERTY = 'battery.remaining_time'
    
    def __init__(self, dbus_utilities = DbusUtils()):
        self._dbus_utilities = dbus_utilities
    
    def add_battery_callback(self, callback_func):
        self._callback_func = callback_func
        try:
            self._register_battery_callback()

            self._ac_adapter_interface = self._dbus_utilities.register_property_listener(self.AC_ADAPTER_TYPE, self._battery_modified)
            
            self._dbus_utilities.add_signal_callback(r'.*battery.*', self._devices_changed)
        except Exception as e:
            log.error("Dbus error", e)
            
        self._battery_modified(0, None)
        
    def get_battery_info(self):
        battery = Battery(None, None, None)
        try:
            if not self._dbus_utilities.has_device_of_type(self.BATTERY_TYPE):
                return battery
    
            remaining = self._dbus_utilities.get_device_property(self.BATTERY_TYPE, self.BATTERY_REMAINING_TIME_PROPERTY)
            level = self._dbus_utilities.get_device_property(self.BATTERY_TYPE, self.BATTERY_PERCENTAGE_PROPERTY)
            charging = self._dbus_utilities.get_device_property(self.AC_ADAPTER_TYPE , self.AC_ADAPTER_PRESENT_PROPERTY)

            battery = Battery(charging, level, remaining)
        except Exception as e:
            print e
            log.error("Battery polling error", e)  
        
        return battery      

    def _devices_changed(self):
        self._register_battery_callback()
        self._callback_func(self.get_battery_info())
            
    def _battery_modified(self, num_changes, property): #@ReservedAssignment
        self._callback_func(self.get_battery_info())

    def _register_battery_callback(self):
        if not hasattr(self, '_is_listener_registered'):
            self._is_listener_registered = True
            self._dbus_utilities.register_property_listener(self.BATTERY_TYPE, self._battery_modified)

class Battery(gtk.EventBox):
    def __init__(self, charging, level, remaining):
        super(Battery, self).__init__()
        self._charging = charging
        self._level = level
        self._remaining = remaining

    def charging(self):
        return self._charging
    
    def level(self):
        return self._level
    
    def time_to_depletion(self):
        return self._remaining
