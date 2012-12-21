from util.dbus_utils import DbusUtils
from eos_util.custom_decorators import consumes_errors
from eos_log import log

class NetworkManager(object):    
    DBUS_NETWORK_MANAGER_PATH = 'org.freedesktop.NetworkManager'
    DBUS_NETWORK_MANAGER_URI = '/org/freedesktop/NetworkManager'
    DBUS_NETWORK_MANAGER_DEVICE_PATH = DBUS_NETWORK_MANAGER_PATH + '.Device'
    DBUS_NETWORK_MANAGER_AP_PATH = DBUS_NETWORK_MANAGER_PATH + '.AccessPoint'
    DBUS_NETWORK_WIRELESS_DEVICE_PATH = DBUS_NETWORK_MANAGER_DEVICE_PATH + '.Wireless' 
    
    DBUS_PROPERTIES_PATH = 'org.freedesktop.DBus.Properties'
    DBUS_PROPERTY_CHANGED_SIGNAL = 'PropertiesChanged'
    
    ACTIVE_WIRELESS_PROPERTY_KEY = 'ActiveAccessPoint'

    NETWORK_DEVICE_TYPE = 'DeviceType'
    WIRELESS_DEVICE = 2

    NETWORK_DEVICE_STATE = 'State'
    DEVICE_CONNECTED = 100
    
    AP_CONNECTION_STRENGTH = 'Strength'
    
    def __init__(self, dbus_util = DbusUtils()):
        self._dbus_util = dbus_util

    def register_device_change_listener(self, callback):
        network_manager_object = self.get_system_bus().get_object(NetworkManager.DBUS_NETWORK_MANAGER_PATH, NetworkManager.DBUS_NETWORK_MANAGER_URI)
        network_manager_object.connect_to_signal(NetworkManager.DBUS_PROPERTY_CHANGED_SIGNAL, callback)
    
    @consumes_errors
    def get_network_state(self):
        wireless_adapter = self._get_first_active_wireless_device()
        if wireless_adapter:
            return self._get_device_strength(wireless_adapter)
        else:
            log.info("No wireless devices found")
    
    def register_ap_callback(self, callback):
        # TODO make sure that signal listeners are destroyed if the device is no longer connected.  
        wireless_adapter = self._get_first_active_wireless_device()
        if wireless_adapter:
            active_access_point_object = self._get_active_access_point_object(wireless_adapter)
            active_access_point_object.connect_to_signal(NetworkManager.DBUS_PROPERTY_CHANGED_SIGNAL, callback)
    
    def _get_device_strength(self, device):
           
        log.debug("Getting strength of" + repr(device))

        active_access_point_object = self._get_active_access_point_object(device)
        active_access_point_properties = active_access_point_object.GetAll(NetworkManager.DBUS_NETWORK_MANAGER_AP_PATH)
        
        strength = int(active_access_point_properties[NetworkManager.AP_CONNECTION_STRENGTH])
        
        print "DEVICE Strength ==== ", strength
        log.debug("Strength is" + repr(strength))
        return strength
    
    def _get_first_active_wireless_device(self):
        for device in self._get_devices():
            if self._is_active_and_connected(device):
                log.debug("Returning wifi device" + repr(device))
                return device
    
    def _get_devices(self):
        self._network_manager = self.get_system_bus().get_object(NetworkManager.DBUS_NETWORK_MANAGER_PATH, NetworkManager.DBUS_NETWORK_MANAGER_URI)
        self._network_manager_interface = self.get_data_bus().Interface(self._network_manager, NetworkManager.DBUS_NETWORK_MANAGER_PATH)
        return self._network_manager_interface.GetDevices()
    
    def _is_active_and_connected(self, device):
        interface = self.get_device_interface(device)
        device_properties = interface.GetAll(NetworkManager.DBUS_NETWORK_MANAGER_DEVICE_PATH)
        
        device_type = device_properties[NetworkManager.NETWORK_DEVICE_TYPE]
        device_state = device_properties[NetworkManager.NETWORK_DEVICE_STATE]
            
        if device_type == NetworkManager.WIRELESS_DEVICE and device_state == NetworkManager.DEVICE_CONNECTED:
            return True
        
        return False
    
    def _get_active_access_point_object(self, adapter):
        adapter_interface = self.get_device_interface(adapter)
        
        wireless_adapter_properties = adapter_interface.GetAll(NetworkManager.DBUS_NETWORK_WIRELESS_DEVICE_PATH)
        
        active_access_point = wireless_adapter_properties[NetworkManager.ACTIVE_WIRELESS_PROPERTY_KEY]
        active_access_point_object = self.get_system_bus().get_object(self.DBUS_NETWORK_MANAGER_PATH, active_access_point)
        
        return active_access_point_object
    
    def get_device_interface(self, device):
        device_object = self.get_system_bus().get_object(NetworkManager.DBUS_NETWORK_MANAGER_PATH, device)
        return self.get_data_bus().Interface(device_object, NetworkManager.DBUS_PROPERTIES_PATH)

    def get_system_bus(self):
        return self._dbus_util.get_system_bus()
    
    def get_data_bus(self):
        return self._dbus_util.get_data_bus()