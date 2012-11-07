import dbus
from eos_log import log
from util import dbus_utils

# TODO where are the tests for this???
# TODO also needs refactoring
class WifiUtil(object):
    @staticmethod
    def get_strength():
        try:
            bus = dbus_utils.DbusUtils().get_system_bus()
            
            # Get a proxy for the base NetworkManager object
            proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
            manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")
            # Get all devices and check if any are wi-fi and are being used
            devices = manager.GetDevices()
            for d in devices:
                dev_proxy = bus.get_object("org.freedesktop.NetworkManager", d)
                prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
                props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device")
                # Wifi device is present
                if props['DeviceType'] == 2:
                    # Wifi device active
                    if props['State'] == 100:
                        wifi_props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device.Wireless")
                        access_point = bus.get_object("org.freedesktop.NetworkManager", wifi_props['ActiveAccessPoint'])
                        ap_props = access_point.GetAll("org.freedesktop.NetworkManager.AccessPoint")
                        return int(ap_props['Strength'])
                # Not a wi-fi device
        except Exception as e:
            log.error("Could not read wifi state", e)
        
        return 0
            
        
        
