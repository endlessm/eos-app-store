import dbus, sys

# This example lists basic information about network interfaces known to NM

devtypes = { 1: "Ethernet",
             2: "Wi-Fi",
             5: "Bluetooth",
             6: "OLPC",
             7: "WiMAX",
             8: "Modem",
             9: "InfiniBand",
             10: "Bond",
             11: "VLAN",
             12: "ADSL" }

states = { 0: "Unknown",
           10: "Unmanaged",
           20: "Unavailable",
           30: "Disconnected",
           40: "Prepare",
           50: "Config",
           60: "Need Auth",
           70: "IP Config",
           80: "IP Check",
           90: "Secondaries",
           100: "Activated",
           110: "Deactivating",
           120: "Failed" }

bus = dbus.SystemBus()

# Get a proxy for the base NetworkManager object
proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")

# Get all devices known to NM and print their properties

#device = manager.GetDeviceByIpIface('eth0')
#dev_proxy = bus.get_object("org.freedesktop.NetworkManager", device)
#prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
#props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device.Wired")
#print props
#print type(device), device
devices = manager.GetDevices()
for d in devices:
    dev_proxy = bus.get_object("org.freedesktop.NetworkManager", d)
    prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
    props = prop_iface.GetAll("org.freedesktop.NetworkManager.Device")
    print "============================"

    print "Interface: %s" % props['Interface']
    try: 
        devtype = devtypes[props['DeviceType']]
    except KeyError:
        devtype = "Unknown"
    print "Type: %s" % devtype

    print "Driver: %s" % props['Driver']

    try:
        state = states[props['State']]
    except KeyError:
        state = "Unknown"
    print "State: %s" % state
    if props['DeviceType'] == 2:
        if props['State'] == 100:
#            check signal strength
            pass
        else:
            pass
#        set icon to "no wifi"
            
            
        
        
