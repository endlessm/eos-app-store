from dbus.glib import DBusGMainLoop
import dbus
import re

from eos_log import log

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
            self._data_bus.glib.init_threads()
            DbusUtils._system_bus = self._data_bus.SystemBus(mainloop = loop)

    def get_system_bus(self):
        return DbusUtils._system_bus
    
    def get_session_bus(self):
        return self._data_bus.SessionBus()

    def register_property_listener(self, device_type, callback):
        interface = self.get_device_interface(device_type)
        interface.connect_to_signal(self.DBUS_PROPERTY_MODIFIED, callback)

    def add_signal_callback(self, regex_match, callback):
        def callback_wrapper(*args, **kwargs):
            for arg in args:
                if re.search(regex_match, arg):
                    callback()

        self.get_system_bus().add_signal_receiver(callback_wrapper, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)

    def has_device_of_type(self, device_type):
        if len(self._get_devices_of_type(device_type)):
            return True
        else:
            return False

    def get_device_property(self, device_type, property_name):
        try:
            return self.get_device_interface(device_type).GetProperty(property_name)
        except Exception as e:
            log.error("Device property retrieval error (" + device_type + ":" + property_name + ")", e)
            return None

    def get_device_interface(self, device_type):
        devices_of_type = self._get_devices_of_type(device_type)
        if len(devices_of_type):
            primary_device = devices_of_type[0]
            device_object = self.get_system_bus().get_object(self.HAL_DBUS_PATH, primary_device)
            return self._data_bus.Interface(device_object, self.HAL_DBUS_DEVICE_PATH)

    def _get_devices_of_type(self, device_type):
        hal_manager = self.get_system_bus().get_object(DbusUtils.HAL_DBUS_PATH, DbusUtils.HAL_DBUS_MANAGER_URI)
        hal_manager_interface = self._data_bus.Interface(hal_manager, DbusUtils.HAL_DBUS_MANAGER_PATH)
        return hal_manager_interface.FindDeviceByCapability(device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)
