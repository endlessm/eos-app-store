from dbus.glib import DBusGMainLoop
import dbus
import re

# TODO test me
class DbusUtils:
    HAL_DBUS_PATH = 'org.freedesktop.Hal'
    HAL_DBUS_MANAGER_URI = '/org/freedesktop/Hal/Manager'
    HAL_DBUS_MANAGER_PATH = HAL_DBUS_PATH + '.Manager'
    HAL_DBUS_DEVICE_PATH = HAL_DBUS_PATH + '.Device'
   
    DBUS_PROPERTY_MODIFIED = 'PropertyModified'
        
    _system_bus = None
    
    def __init__(self, data_bus = dbus):
        self._data_bus = data_bus
        
        if DbusUtils._system_bus is None:
            loop = DBusGMainLoop(set_as_default=True) 
            dbus.glib.init_threads()
            DbusUtils._system_bus = dbus.SystemBus(mainloop = loop)
    
    def get_system_bus(self):
        return DbusUtils._system_bus

    def register_property_listener(self, device_type, callback):
        hal_manager = self.get_system_bus().get_object(DbusUtils.HAL_DBUS_PATH, DbusUtils.HAL_DBUS_MANAGER_URI)
        hal_manager_interface = self._data_bus.Interface(hal_manager, 
                                                         DbusUtils.HAL_DBUS_MANAGER_PATH)
        
        devices_of_type = hal_manager_interface.FindDeviceByCapability(device_type, 
                                                                       dbus_interface=self.HAL_DBUS_MANAGER_PATH)
        if len(devices_of_type):
            primary_device = devices_of_type[0]
            device_interface = self._data_bus.Interface(self.get_system_bus().get_object(self.HAL_DBUS_PATH, 
                                                                                         primary_device), 
                                                                                         self.HAL_DBUS_DEVICE_PATH)
            device_interface.connect_to_signal(self.DBUS_PROPERTY_MODIFIED, 
                                               callback)
            
            return device_interface
        
    def add_signal_callback(self, regex_match, callback):
        def callback_wrapper(self, *args, **kwargs):
            for arg in args:
                if re.search(regex_match, arg):
                    callback()

        self.get_system_bus().add_signal_receiver(callback_wrapper, 
                                                  dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)
        
    def has_device_of_type(self, device_type):
        self._hal_manager_interface.FindDeviceByCapability(device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)
        
    def get_device_property(self, interface, property_name):
        try:
            return interface.GetProperty(property_name)
        except:
            return None
