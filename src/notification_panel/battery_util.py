import dbus

class BatteryUtil():
    HAL_DBUS_PATH = 'org.freedesktop.Hal'
    HAL_DBUS_MANAGER_URI = '/org/freedesktop/Hal/Manager'
    HAL_DBUS_MANAGER_PATH = HAL_DBUS_PATH + '.Manager'
    HAL_DBUS_DEVICE_PATH = HAL_DBUS_PATH + '.Device'
    
    @staticmethod
    def get_battery_level(data_bus = dbus):
        bus = data_bus.SystemBus()
        hal_manager = bus.get_object(BatteryUtil.HAL_DBUS_PATH, BatteryUtil.HAL_DBUS_MANAGER_URI)
        hal_manager_interface = data_bus.Interface (hal_manager, BatteryUtil.HAL_DBUS_MANAGER_PATH)
        
        batteries = hal_manager_interface.FindDeviceByCapability('battery', dbus_interface=BatteryUtil.HAL_DBUS_MANAGER_PATH)
        
        battery_level = None
        if len(batteries) > 0:
            battery_object = bus.get_object(BatteryUtil.HAL_DBUS_PATH, batteries[0])
            battery_interface = data_bus.Interface (battery_object, BatteryUtil.HAL_DBUS_DEVICE_PATH)

            # TODO add recharging/discharging data
            # if(interface.GetProperty('battery.rechargeable.is_discharging') == 0):
            # if ( interface.GetProperty('battery.is_rechargeable') ):
            
            battery_level = battery_interface.GetProperty('battery.charge_level.percentage')
            
        return battery_level