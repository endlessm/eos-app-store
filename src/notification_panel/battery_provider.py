import dbus
import sys
import gtk
import gobject

class BatteryProvider():
    HAL_DBUS_PATH = 'org.freedesktop.Hal'
    HAL_DBUS_MANAGER_URI = '/org/freedesktop/Hal/Manager'
    HAL_DBUS_MANAGER_PATH = HAL_DBUS_PATH + '.Manager'
    HAL_DBUS_DEVICE_PATH = HAL_DBUS_PATH + '.Device'
    
    BATTERY_DISCHARGING_PROPERTY = 'battery.rechargeable.is_discharging'
    BATTERY_PERCENTAGE_PROPERTY = 'battery.charge_level.percentage'
    BATTERY_REMAINING_TIME_PROPERTY = 'battery.remaining_time'
    
    def __init__(self, data_bus = dbus):
        self._data_bus = data_bus
        self._system_bus = self._data_bus.SystemBus()
        self._hal_manager = self._system_bus.get_object(BatteryProvider.HAL_DBUS_PATH, BatteryProvider.HAL_DBUS_MANAGER_URI)
        self._hal_manager_interface = data_bus.Interface (self._hal_manager, BatteryProvider.HAL_DBUS_MANAGER_PATH)
        
    def get_battery(self):
        battery = Battery(None, None, None)
        try:
            batteries = self._hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=BatteryProvider.HAL_DBUS_MANAGER_PATH)
            
            if len(batteries):
                primary_battery = batteries[0]
                battery_interface = self._data_bus.Interface(self._system_bus.get_object(BatteryProvider.HAL_DBUS_PATH, primary_battery), BatteryProvider.HAL_DBUS_DEVICE_PATH)
                discharging = battery_interface.GetProperty(self.BATTERY_DISCHARGING_PROPERTY)
                level = battery_interface.GetProperty(self.BATTERY_PERCENTAGE_PROPERTY)
#                We saw an interesting situation occur only one time after a few full days of testing:
#                dbus could not find a 'remaining_time' property on the battery.  After restarting, 
#                the property was present again
                remaining = battery_interface.GetProperty(self.BATTERY_REMAINING_TIME_PROPERTY)
                battery = Battery(not discharging, level, remaining)
        except:
            pass
        return battery

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
