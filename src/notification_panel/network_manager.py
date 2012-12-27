from dbus_foo import Dbus

class NetworkManager():
    SERVICE_PATH = 'org.freedesktop.NetworkManager'
    OBJECT_PATH = '/org/freedesktop/NetworkManager'
    INTERFACE_PATH = 'org.freedesktop.NetworkManager'
    DBUS_PROPERTIES_PATH = 'org.freedesktop.DBus.Properties'

    DBUS_NETWORK_MANAGER_PATH = 'org.freedesktop.NetworkManager'
    DBUS_NETWORK_MANAGER_URI = '/org/freedesktop/NetworkManager'
    DBUS_NETWORK_MANAGER_SETTINGS_URI = DBUS_NETWORK_MANAGER_URI + '/Settings'
    DBUS_NETWORK_MANAGER_DEVICE_PATH = DBUS_NETWORK_MANAGER_PATH + '.Device'
    DBUS_NETWORK_MANAGER_SETTINGS_PATH = DBUS_NETWORK_MANAGER_PATH + '.Settings'
    DBUS_NETWORK_MANAGER_AP_PATH = DBUS_NETWORK_MANAGER_PATH + '.AccessPoint'
    DBUS_NETWORK_WIRELESS_DEVICE_PATH = DBUS_NETWORK_MANAGER_DEVICE_PATH + '.Wireless' 
    NETWORK_DEVICE_TYPE = 'DeviceType'
    WIRELESS_DEVICE = 2

    NETWORK_DEVICE_STATE = 'State'
    DEVICE_CONNECTED = 100
    
    ACTIVE_WIRELESS_PROPERTY_KEY = 'ActiveAccessPoint'
    AP_CONNECTION_STRENGTH = 'Strength'

    PROPERTIES_CHANGED = 'PropertiesChanged'
    
    @classmethod
    def from_dbus(cls, get_interface=Dbus().get_interface):
        interface = get_interface(cls.SERVICE_PATH, cls.OBJECT_PATH, cls.INTERFACE_PATH)

        return NetworkManager(interface, get_interface)

    @classmethod
    def _is_active_and_connected(cls, device, get_interface):
        device_properties = device.GetAll(cls.DBUS_NETWORK_MANAGER_DEVICE_PATH)
        
        # Although we have a device, there may not be an active connection running on it 
        device_connection = device_properties["ActiveConnection"]
        if str(device_connection) == '/':
            return False
            
        # is the wireless device connected, and selected by the OS as the default connection?
        device_type = device_properties[cls.NETWORK_DEVICE_TYPE]
        device_state = device_properties[cls.NETWORK_DEVICE_STATE]
        return device_type == cls.WIRELESS_DEVICE and device_state == cls.DEVICE_CONNECTED

    
    def __init__(self, _interface, _get_interface):
        self._listeners = []
        self._ap_properties_changed_signal = None
        self._get_interface = _get_interface
        self._interface = _interface
        self._network_properties_changed_signal = _interface.connect_to_signal(self.PROPERTIES_CHANGED, self.retrieve_state)

    def __eq__(self, other):
        return other._device_interface == self._device_interface
    
    def add_state_changed_listener(self, callback):
        '''
          registers a callback for when the state of the network manager changes.
          ie. not connected to connected
        '''
        self._listeners.append(callback)
    
    def retrieve_state(self, args = None):
        if self._ap_properties_changed_signal is not None:
            self._ap_properties_changed_signal.remove()
            
        active_device_interface = None
        active_device_path = None
        for device in self._interface.GetDevices():
            device_interface = self._get_interface(self.SERVICE_PATH, device, self.DBUS_PROPERTIES_PATH)
            if NetworkManager._is_active_and_connected(device_interface, self._get_interface):
                active_device_path = device
                active_device_interface = device_interface
        
        self._ap_interface = None
        if active_device_interface:
            device_properties_interface = self._get_interface(self.SERVICE_PATH, active_device_path, self.DBUS_PROPERTIES_PATH)
            ap_path = device_properties_interface.Get(self.DBUS_NETWORK_WIRELESS_DEVICE_PATH, NetworkManager.ACTIVE_WIRELESS_PROPERTY_KEY)
            self._ap_interface = self._get_interface(self.SERVICE_PATH, ap_path, self.DBUS_PROPERTIES_PATH) 
            self._ap_properties_changed_signal = self._ap_interface.connect_to_signal(self.PROPERTIES_CHANGED, self.notify_listeners)
        
        self.notify_listeners()

    def notify_listeners(self):
        self._broadcast_network_state(self.get_state_from_dbus())
    
    def get_state_from_dbus(self):
        strength = 0
        if self._ap_interface:
            strength_property = self._ap_interface.Get(self.DBUS_NETWORK_MANAGER_AP_PATH, self.AP_CONNECTION_STRENGTH)
            strength = int(strength_property)
        return strength
    
    def _broadcast_network_state(self, state):
        for listener in self._listeners:
            listener(state)
    
#    def display_strength_on(self, callback):
#        self.active_device().display_strength_on(callback)
    
#    def display_state_on(self, callback):
#        self._state().display_on(callback)
#        
#    def _state(self):
#        return State(self._interface.state())

    #class State():
    #    enum = {
    #              0  : "unknown",
    #              10 : "inactive",
    #              20 : "disconnected",
    #              30 : "disconnecting",
    #              40 : "connecting",
    #              50 : "link-local connectivity",
    #              60 : "site-local connectivity",
    #              70 : "connected",
    #           }
    #    
    #    def __init__(self, value):
    #        self.value = value
    #        
    #    def display_on(self, callback):
    #        callback(str(self))
    #        
    #    def __str__(self):
    #        return self.enum[self.value]
    #    
    #    def __eq__(self, other):
    #        return other.value == self.value

#NM_STATE_UNKNOWN = 0
#    Networking state is unknown. 
#NM_STATE_ASLEEP = 10
#    Networking is inactive and all devices are disabled. 
#NM_STATE_DISCONNECTED = 20
#    There is no active network connection. 
#NM_STATE_DISCONNECTING = 30
#    Network connections are being cleaned up. 
#NM_STATE_CONNECTING = 40
#    A network device is connecting to a network and there is no other available network connection. 
#NM_STATE_CONNECTED_LOCAL = 50
#    A network device is connected, but there is only link-local connectivity. 
#NM_STATE_CONNECTED_SITE = 60
#    A network device is connected, but there is only site-local connectivity. 
#NM_STATE_CONNECTED_GLOBAL = 70
#    A network device is connected, with global network connectivity. 