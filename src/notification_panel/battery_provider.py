import dbus
import gtk

from eos_log import log
from util.dbus_utils import DbusUtils
import re

#TODO test me
class BatteryProvider():
    HAL_DBUS_PATH = 'org.freedesktop.Hal'
    HAL_DBUS_MANAGER_URI = '/org/freedesktop/Hal/Manager'
    HAL_DBUS_MANAGER_PATH = HAL_DBUS_PATH + '.Manager'
    HAL_DBUS_DEVICE_PATH = HAL_DBUS_PATH + '.Device'
    
    DBUS_PROPERTY_MODIFIED = 'PropertyModified'
    
    AC_ADAPTER_PRESENT = 'ac_adapter.present'
    
    BATTERY_DISCHARGING_PROPERTY = 'battery.rechargeable.is_discharging'
    BATTERY_PERCENTAGE_PROPERTY = 'battery.charge_level.percentage'
    BATTERY_REMAINING_TIME_PROPERTY = 'battery.remaining_time'
    
    def __init__(self, data_bus = dbus, dbus_utilities = DbusUtils()):
        self._data_bus = data_bus

        self._system_bus = dbus_utilities.get_system_bus()
        self._hal_manager = self._system_bus.get_object(BatteryProvider.HAL_DBUS_PATH, BatteryProvider.HAL_DBUS_MANAGER_URI)
        self._hal_manager_interface = data_bus.Interface (self._hal_manager, BatteryProvider.HAL_DBUS_MANAGER_PATH)
        
        self._battery_interface = None
    
    def add_battery_callback(self, callback_func):
        self._callback_func = callback_func
        try:
            self._register_battery_callback()
            
            # Register listener for AC adapter changes
            ac_adapters = self._hal_manager_interface.FindDeviceByCapability('ac_adapter', dbus_interface=self.HAL_DBUS_MANAGER_PATH)
            if len(ac_adapters):
                primary_ac_adapter = ac_adapters[0]
                self._ac_adapter_interface = self._data_bus.Interface(self._system_bus.get_object(self.HAL_DBUS_PATH, primary_ac_adapter), self.HAL_DBUS_DEVICE_PATH)
                self._ac_adapter_interface.connect_to_signal(self.DBUS_PROPERTY_MODIFIED, self._battery_modified)
                
            self._system_bus.add_signal_receiver(self._handle_hal_event, dbus_interface=self.HAL_DBUS_MANAGER_PATH)
        except Exception as e:
            log.error("Dbus error", e)
            
        self._battery_modified(0, None)
        
    def get_battery_info(self):
        battery = Battery(None, None, None)
        try:
            batteries = self._hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=BatteryProvider.HAL_DBUS_MANAGER_PATH)
            if not len(batteries):
                return battery
    
            # Full battery throws this exception  
            remaining = None
            try:
                remaining = self._battery_interface.GetProperty(self.BATTERY_REMAINING_TIME_PROPERTY)
            except:
                pass
            
            discharging = not self._ac_adapter_interface.GetProperty(self.AC_ADAPTER_PRESENT)
            level = self._battery_interface.GetProperty(self.BATTERY_PERCENTAGE_PROPERTY)

            battery = Battery(not discharging, level, remaining)
        except Exception as e:
            log.error("Battery polling error", e)  
        
        return battery      
            
    # Register listener for battery changes
    def _register_battery_callback(self):
        if self._battery_interface:
            return
        
        batteries = self._hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=self.HAL_DBUS_MANAGER_PATH)
        if len(batteries):
            primary_battery = batteries[0]
            self._battery_interface = self._data_bus.Interface(self._system_bus.get_object(self.HAL_DBUS_PATH, primary_battery), self.HAL_DBUS_DEVICE_PATH)
            self._battery_interface.connect_to_signal(self.DBUS_PROPERTY_MODIFIED, self._battery_modified)
            
    # if battery plugged in, register listener for its status
    def _handle_hal_event(self, *args, **kwargs):
        for arg in args:
            if re.search(r'.*battery.*', arg):
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
