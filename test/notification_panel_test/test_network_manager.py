import unittest
from mock import Mock, call
from notification_panel.network_manager import *

class NetworkManagerTestCase(unittest.TestCase):
    
    def test_dbus_constants(self):
        service_path = 'org.freedesktop.NetworkManager'
        object_path = '/org/freedesktop/NetworkManager'
        interface_path = 'org.freedesktop.NetworkManager'
        network_state_changed = 'PropertiesChanged'
        
        self.assertEquals(NetworkManager.SERVICE_PATH, service_path)
        self.assertEquals(NetworkManager.OBJECT_PATH, object_path)
        self.assertEquals(NetworkManager.INTERFACE_PATH, interface_path)
        self.assertEquals(NetworkManager.NETWORK_STATE_CHANGED, network_state_changed)

    def test_create_from_dbus_where_no_active_wireless_devices(self):
        interface = Mock()
        interface.GetDevices = Mock(return_value=[])
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        get_interface.assert_was_called_once_with(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH)
        
        self.assertEquals(network_manager, NetworkManager(None, Mock()))
        
    def test_create_from_dbus_where_active_network_isnt_wireless(self):
        interface = Mock()
        device = Mock()
        all_properties = {NetworkManager.NETWORK_DEVICE_TYPE: 'non-wireless', NetworkManager.NETWORK_DEVICE_STATE: ''}
        interface.GetDevices = Mock(return_value=[device])
        interface.GetAll = Mock(return_value=all_properties)
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        interface_calls = [call(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH), 
                           call(NetworkManager.SERVICE_PATH, device, NetworkManager.DBUS_PROPERTIES_PATH)]
        get_interface.assert_has_calls(interface_calls)
        
        self.assertEquals(network_manager, NetworkManager(None, Mock()))

    def test_create_from_dbus_where_active_network_is_wireless_but_not_connected(self):
        interface = Mock()
        device = Mock()
        all_properties = {NetworkManager.NETWORK_DEVICE_TYPE: NetworkManager.WIRELESS_DEVICE, NetworkManager.NETWORK_DEVICE_STATE: ''}
        interface.GetDevices = Mock(return_value=[device])
        interface.GetAll = Mock(return_value=all_properties)
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        interface_calls = [call(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH), 
                           call(NetworkManager.SERVICE_PATH, device, NetworkManager.DBUS_PROPERTIES_PATH)]
        get_interface.assert_has_calls(interface_calls)
        
        self.assertEquals(network_manager, NetworkManager(None, Mock()))

    def test_create_from_dbus_where_wireless_is_connected(self):
        interface = Mock()
        device = Mock()
        all_properties = {NetworkManager.NETWORK_DEVICE_TYPE: NetworkManager.WIRELESS_DEVICE, 
                          NetworkManager.NETWORK_DEVICE_STATE: NetworkManager.DEVICE_CONNECTED}
        device_properties = {NetworkManager.ACTIVE_WIRELESS_PROPERTY_KEY: 'wireless-device-uri'}
        interface.GetDevices = Mock(return_value=[device])
        interface.GetAll = Mock(return_value=all_properties)
        device.GetAll = Mock(return_value=device_properties)
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        interface_calls = [call(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH), 
                           call(NetworkManager.SERVICE_PATH, device, NetworkManager.DBUS_PROPERTIES_PATH),
                           call(NetworkManager.SERVICE_PATH, NetworkManager.DBUS_NETWORK_MANAGER_PATH, 'wireless-device-uri')]
        get_interface.assert_has_calls(interface_calls)
        
        self.assertEquals(network_manager, NetworkManager(device, Mock()))

    def test_add_state_changed_listener(self):
        interface = Mock()
        test_object = NetworkManager(interface, Mock())
        callback = Mock()
        
        test_object.add_state_changed_listener(callback)
        
        self.assertEquals(callback,test_object._listeners[0]) 
        
    def test_retrieve_state_broadcasts_data_to_listeners(self):
        callback = Mock()
        network_state = Mock()
        test_object = NetworkManager(Mock(), Mock())
        test_object.get_state_from_dbus = Mock(return_value=network_state)
        test_object.add_state_changed_listener(callback)

        test_object.retrieve_state()
        
        callback.assert_called_once_with(network_state)
        
    def test_getting_current_state_from_dbus(self):
        interface = Mock()
        test_object = NetworkManager(interface, Mock())

        network_state = test_object.get_state_from_dbus()
        
        self.assertIsNotNone(network_state)
