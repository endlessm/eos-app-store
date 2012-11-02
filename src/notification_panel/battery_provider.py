import dbus
import gtk

from eos_log import log
from util.dbus_utils import DbusUtils
import re

#TODO test me
class BatteryProvider():
    AC_ADAPTER_PRESENT = 'ac_adapter.present'
    
    BATTERY_DISCHARGING_PROPERTY = 'battery.rechargeable.is_discharging'
    BATTERY_PERCENTAGE_PROPERTY = 'battery.charge_level.percentage'
    BATTERY_REMAINING_TIME_PROPERTY = 'battery.remaining_time'
    
    def __init__(self, dbus_utilities = DbusUtils()):
        self._dbus_utilities = dbus_utilities
        
        self._battery_interface = None
    
    def add_battery_callback(self, callback_func):
        self._callback_func = callback_func
        try:
            self._register_battery_callback()
            
            self._ac_adapter_interface = self._dbus_utilities.register_property_listener('ac_adapter', self._battery_modified)
            
            self._dbus_utilities.add_signal_callback(r'.*battery.*', self._handle_hal_event)
        except Exception as e:
            log.error("Dbus error", e)
            
        self._battery_modified(0, None)
        
    def get_battery_info(self):
        battery = Battery(None, None, None)
        try:
            if not self._dbus_utilities.has_device_of_type('battery'):
                return battery
    
            # Full battery throws this exception  
            remaining = None
            try:
                remaining = self._dbus_utilities.get_device_property(self._battery_interface, self.BATTERY_REMAINING_TIME_PROPERTY)
            except:
                pass
            
            discharging = not self._dbus_utilities.get_device_property(self._ac_adapter_interface, self.AC_ADAPTER_PRESENT)
            level = self._dbus_utilities.get_device_property(self._battery_interface, self.BATTERY_PERCENTAGE_PROPERTY)

            battery = Battery(not discharging, level, remaining)
        except Exception as e:
            log.error("Battery polling error", e)  
        
        return battery      
            
    # Register listener for battery changes
    def _register_battery_callback(self):
        if self._battery_interface:
            return
        
        self._battery_interface = self._dbus_utilities.register_property_listener('battery', self._battery_modified)
    
    
    
    # if battery plugged in, register listener for its status
    def _handle_hal_event(self):
            self._register_battery_callback()
            self._battery_modified(0, None)
        
    def _battery_modified(self, num_changes, property): #@ReservedAssignment
        self._callback_func(self.get_battery_info())

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
