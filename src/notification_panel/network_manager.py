from dbus_foo import Dbus
from ui.abstract_notifier import AbstractNotifier

class NetworkManager():
    SERVICE_PATH = 'org.freedesktop.NetworkManager'
    OBJECT_PATH = '/org/freedesktop/NetworkManager'
    INTERFACE_PATH = 'org.freedesktop.NetworkManager'
    
    NETWORK_STATE_CHANGED = 'PropertiesChanged'
    
    @classmethod
    def from_dbus(cls, get_interface=Dbus().get_interface):
        interface = get_interface(cls.SERVICE_PATH, cls.OBJECT_PATH, cls.INTERFACE_PATH)
        return NetworkManager(interface)
    
    def __init__(self, _interface):
        self._interface = _interface
    
    def __eq__(self, other):
        return other._interface == self._interface
    
    def add_state_changed_listener(self, callback):
        '''
          registers a callback for when the state of the network manager changes.
          ie. not connected to connected
        '''
        self._interface.connect_to_signal(self.NETWORK_STATE_CHANGED, callback)
    
    def display_strength_on(self, callback):
        callback(0)
    
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