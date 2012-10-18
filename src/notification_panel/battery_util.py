import dbus
import sys
import gtk
import gobject

class BatteryUtil():
    HAL_DBUS_PATH = 'org.freedesktop.Hal'
    HAL_DBUS_MANAGER_URI = '/org/freedesktop/Hal/Manager'
    HAL_DBUS_MANAGER_PATH = HAL_DBUS_PATH + '.Manager'
    HAL_DBUS_DEVICE_PATH = HAL_DBUS_PATH + '.Device'
    
    BATTERY_DISCHARGING_PROPERTY = 'battery.rechargeable.is_discharging'
    BATTERY_PERCENTAGE_PROPERTY = 'battery.charge_level.percentage'
    
    @staticmethod
    def get_battery_level(data_bus = dbus):
        battery_level = None
        is_recharging = None

        try:
            bus = data_bus.SystemBus()
            hal_manager = bus.get_object(BatteryUtil.HAL_DBUS_PATH, BatteryUtil.HAL_DBUS_MANAGER_URI)
            hal_manager_interface = data_bus.Interface (hal_manager, BatteryUtil.HAL_DBUS_MANAGER_PATH)
            
            batteries = hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=BatteryUtil.HAL_DBUS_MANAGER_PATH)
            
            if len(batteries) > 0:
                battery_object = bus.get_object(BatteryUtil.HAL_DBUS_PATH, batteries[0])
                battery_interface = data_bus.Interface (battery_object, BatteryUtil.HAL_DBUS_DEVICE_PATH)
                
#                print "Remaining time: ", battery_interface.GetProperty('battery.remaining_time')
                
                is_recharging = not battery_interface.GetProperty(BatteryUtil.BATTERY_DISCHARGING_PROPERTY)
                battery_level = battery_interface.GetProperty(BatteryUtil.BATTERY_PERCENTAGE_PROPERTY)
        except:
            battery_level = None
            is_recharging = None
           
        return battery_level, is_recharging
    
    @staticmethod
    def get_battery(data_bus = dbus):
        battery = NoBattery()
        try:
            bus = data_bus.SystemBus()
            hal_manager = bus.get_object(BatteryUtil.HAL_DBUS_PATH, BatteryUtil.HAL_DBUS_MANAGER_URI)
            hal_manager_interface = data_bus.Interface (hal_manager, BatteryUtil.HAL_DBUS_MANAGER_PATH)
            
            batteries = hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=BatteryUtil.HAL_DBUS_MANAGER_PATH)
            
            if len(batteries):
                battery = Battery(batteries)
        except:
            pass
        return battery

class NoBattery():
    def init(self, gobj=gobject):
        pass
    
    def draw(self, presenter):
        pass

class Battery(gtk.EventBox):
    def __init__(self, batteries, gobj=gobject):
        super(Battery, self).__init__()
        self._data_bus = dbus
        self._system_bus = self._data_bus.SystemBus()
        self._batteries = batteries
    
    def register(self, presenter):
#        print "level", self.level()
#        print "charging", self.charging()
        try:
            presenter._update_battery_indicator(self)
        except:
            presenter.battery_disconnected()
        
    
    def charging(self):
        return not self._battery_interface().GetProperty(BatteryUtil.BATTERY_DISCHARGING_PROPERTY)
    
    def level(self):
        return self._battery_interface().GetProperty(BatteryUtil.BATTERY_PERCENTAGE_PROPERTY)
    
    def _battery_object(self):
        return self._system_bus.get_object(BatteryUtil.HAL_DBUS_PATH, self._batteries[0])
    
    def _battery_interface(self):
        return self._data_bus.Interface(self._battery_object(), BatteryUtil.HAL_DBUS_DEVICE_PATH)
        
        
        