import unittest
from mock import Mock
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

    def test_create_from_dbus(self):
        interface = Mock()
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        get_interface.assert_was_called_once_with(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH)
        
        self.assertEquals(network_manager, NetworkManager(interface))
        
    def test_add_state_changed_listener(self):
        interface = Mock()
        test_object = NetworkManager(interface)
        callback = Mock()
        
        test_object.add_state_changed_listener(callback)
        
        interface.connect_to_signal.assert_called_once_with(NetworkManager.NETWORK_STATE_CHANGED, callback)
        
