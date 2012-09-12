import dbus

class WifiUtil(object):

    @staticmethod
    def get_strength():
        bus = dbus.SystemBus()
        
        # Get a proxy for the base NetworkManager object
        proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
        manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")
        # Get all devices and check if any are wi-fi and are being used
        devices = manager.GetDevices()
        for d in devices:
            dev_proxy = bus.get_object("org.freedesktop.NetworkManager", d)
            prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
            props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device")
        #   wi-fi device is present
            if props['DeviceType'] == 2:
        #       wi-fi is device active
                if props['State'] == 100:
                    wifi_props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device.Wireless")
#                    print wifi_props
#                    print "Access Point = ", wifi_props['ActiveAccessPoint']
                    access_point = bus.get_object("org.freedesktop.NetworkManager", wifi_props['ActiveAccessPoint'])
                    ap_props = access_point.GetAll("org.freedesktop.NetworkManager.AccessPoint")
#                    print "The strength = ", int(ap_props['Strength'])
                    return int(ap_props['Strength'])
        #   not a wi-fi device
        return 0
        print "Not using wifi boooo"        
            
        
        
