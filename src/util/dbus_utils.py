from dbus.glib import DBusGMainLoop
import dbus

# TODO test me
class DbusUtils:
    _system_bus = None
    
    @staticmethod
    def get_system_bus():
        if DbusUtils._system_bus is None:
            loop = DBusGMainLoop(set_as_default=True) 
            dbus.glib.init_threads()
            DbusUtils._system_bus = dbus.SystemBus(mainloop = loop)
            
        return DbusUtils._system_bus