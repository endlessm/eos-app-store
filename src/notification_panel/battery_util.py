import dbus
import sys

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
                
                is_recharging = False
                if(battery_interface.GetProperty(BatteryUtil.BATTERY_DISCHARGING_PROPERTY) == 0):
                    is_recharging = True
                battery_level = battery_interface.GetProperty(BatteryUtil.BATTERY_PERCENTAGE_PROPERTY)
        except:
            battery_level = None
            is_recharging = None
           
        return battery_level, is_recharging
