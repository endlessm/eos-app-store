from util.dbus_utils import DbusUtils
import dbus

class Dbus():
    
    def __init__(self, _dbus = dbus, _system_bus = DbusUtils().get_system_bus()):
        self._dbus = _dbus
        self._system_bus = _system_bus

    def get_interface(self, service_path, object_path, interface_path):
        struct = self._system_bus.get_object(service_path, object_path)
        return self._dbus.Interface(struct, interface_path)