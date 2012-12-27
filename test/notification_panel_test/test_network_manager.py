import unittest
from mock import Mock, call
from notification_panel.network_manager import *

class NetworkManagerTestCase(unittest.TestCase):
    
    def test_create_from_dbus(self):
        interface = Mock()
        get_interface = Mock(return_value=interface)
        
        network_manager = NetworkManager.from_dbus(get_interface)
        
        get_interface.assert_was_called_once_with(NetworkManager.SERVICE_PATH, NetworkManager.OBJECT_PATH, NetworkManager.INTERFACE_PATH)
        
        self.assertIsNotNone(network_manager)
        self.assertEquals(NetworkManager(interface, get_interface), network_manager)
        
    def test_add_state_changed_listener(self):
        interface = Mock()
        test_object = NetworkManager(interface, Mock())
        callback = Mock()
        
        test_object.add_state_changed_listener(callback)
        
        self.assertEquals(callback,test_object._listeners[0]) 

    def test_notify_broadcasts_data_to_listeners(self):
        callback = Mock()
        network_state = Mock()
        test_object = NetworkManager(Mock(), Mock())
        test_object.get_state_from_dbus = Mock(return_value=network_state)
        test_object.add_state_changed_listener(callback)

        test_object.notify_listeners()
        
        callback.assert_called_once_with(network_state)

    def test_network_device_with_no_active_connection(self):
        interface = Mock()
        device = Mock()
        device_props = {'ActiveConnection': '/'}
        device.GetAll = Mock(return_value=device_props)
        get_interface = Mock(return_value=interface)
        network_manager = NetworkManager(interface, get_interface)
        
        self.assertFalse(network_manager.is_active_and_connected(device, get_interface))
        device.GetAll.assert_called_once_with(NetworkManager.DBUS_NETWORK_MANAGER_DEVICE_PATH)
        
    def test_wired_device_active_with_active_connection(self):
        interface = Mock()
        device = Mock()
        device_props = {'ActiveConnection': 'connection', 
                        NetworkManager.NETWORK_DEVICE_TYPE: 1, 
                        NetworkManager.NETWORK_DEVICE_STATE: NetworkManager.DEVICE_CONNECTED}
        device.GetAll = Mock(return_value=device_props)
        get_interface = Mock(return_value=interface)
        network_manager = NetworkManager(interface, get_interface)
        
        self.assertFalse(network_manager.is_active_and_connected(device, get_interface))
        device.GetAll.assert_called_once_with(NetworkManager.DBUS_NETWORK_MANAGER_DEVICE_PATH)

    def test_wireless_device_active_with_active_connection(self):
        interface = Mock()
        device = Mock()
        device_props = {'ActiveConnection': 'connection', 
                        NetworkManager.NETWORK_DEVICE_TYPE: 2, 
                        NetworkManager.NETWORK_DEVICE_STATE: NetworkManager.DEVICE_CONNECTED}
        device.GetAll = Mock(return_value=device_props)
        get_interface = Mock(return_value=interface)
        network_manager = NetworkManager(interface, get_interface)
        
        self.assertTrue(network_manager.is_active_and_connected(device, get_interface))
        device.GetAll.assert_called_once_with(NetworkManager.DBUS_NETWORK_MANAGER_DEVICE_PATH)
        
    def test_disconnect_ap_signal(self):
        interface = Mock()
        get_interface = Mock(return_value=Mock())
        network_manager = NetworkManager(interface, get_interface)
        signal = Mock()
        network_manager._ap_properties_changed_signal = signal
        
        network_manager._disconnect_ap_signal()
        
        signal.remove.assert_called_once_with()
        self.assertIsNone(network_manager._ap_properties_changed_signal)

    def test_connect_ap_signal(self):
        interface = Mock()
        get_interface = Mock(return_value=Mock())
        network_manager = NetworkManager(interface, get_interface)
        network_manager._ap_interface = Mock()
        signal = Mock()
        network_manager._ap_interface.connect_to_signal = Mock(return_value=signal)
        
        network_manager._connect_ap_signal()
        
        network_manager._ap_interface.connect_to_signal.assert_called_once_with(NetworkManager.PROPERTIES_CHANGED, network_manager.notify_listeners)
        self.assertEquals(signal, network_manager._ap_properties_changed_signal)
        
    def test_no_ap_found_when_no_active_device(self):
        interface = Mock()
        get_interface = Mock(return_value=Mock())
        network_manager = NetworkManager(interface, get_interface)
        
        self.assertIsNone(network_manager._find_ap_interface(None, None))
        
    def test_find_ap_when_for_active_device(self):
        interface = Mock()
        properties_interface = Mock()
        ap_path = Mock()
        properties_interface.Get = Mock(return_value=ap_path)
        get_interface = Mock(return_value=properties_interface)
        network_manager = NetworkManager(interface, get_interface)
        active_device_interface = Mock()
        active_device_path = 'device_path'

        result = network_manager._find_ap_interface(active_device_interface, active_device_path)
        
        calls = [call(NetworkManager.SERVICE_PATH, active_device_path, NetworkManager.DBUS_PROPERTIES_PATH), 
                 call(NetworkManager.SERVICE_PATH, ap_path, NetworkManager.DBUS_PROPERTIES_PATH)]        
        
        get_interface.assert_has_calls(calls)
        self.assertEquals(properties_interface, result)
        
    def test_no_wireless_devices(self):
        interface = Mock()
        interface.GetDevices = Mock(return_value=[])
        network_manager = NetworkManager(interface, Mock())
        
        device_interface, device_path = network_manager.find_active_wireless_devices()
        
        self.assertIsNone(device_interface)
        self.assertIsNone(device_path)
        
    def test_no_active_connected_wireless_devices(self):
        interface = Mock()
        interface.GetDevices = Mock(return_value=['foo'])
        get_interface = Mock()
        network_manager = NetworkManager(interface, get_interface)
        network_manager.is_active_and_connected = Mock(return_value=False)
        
        device_interface, device_path = network_manager.find_active_wireless_devices()
        
        get_interface.assert_called_once_with(NetworkManager.SERVICE_PATH, 'foo', NetworkManager.DBUS_PROPERTIES_PATH)
        
        self.assertIsNone(device_interface)
        self.assertIsNone(device_path)

    def test_active_connected_wireless_device(self):
        interface = Mock()
        interface.GetDevices = Mock(return_value=['foo'])
        an_interface = Mock()
        get_interface = Mock(return_value=an_interface)
        network_manager = NetworkManager(interface, get_interface)
        network_manager.is_active_and_connected = Mock(return_value=True)
        
        device_interface, device_path = network_manager.find_active_wireless_devices()
        
        get_interface.assert_called_once_with(NetworkManager.SERVICE_PATH, 'foo', NetworkManager.DBUS_PROPERTIES_PATH)
        
        self.assertEquals(an_interface, device_interface)
        self.assertEquals('foo', device_path)
        
    def test_retrieve_state_calls_the_whole_world(self):
        network_manager = NetworkManager(Mock(), Mock())
        iface = Mock()
        path = Mock()
        network_manager._disconnect_ap_signal = Mock()
        network_manager.find_active_wireless_devices = Mock(return_value=(iface, path))
        network_manager._find_ap_interface = Mock(return_value=Mock())
        network_manager._connect_ap_signal = Mock()
        network_manager.notify_listeners = Mock()
        
        network_manager.retrieve_state()
        
        network_manager._disconnect_ap_signal.assert_called_once_with()
        network_manager.find_active_wireless_devices.assert_called_once_with()
        network_manager._find_ap_interface.assert_called_once_with(iface, path)
        network_manager._connect_ap_signal.assert_called_once_with()
        network_manager.notify_listeners.assert_called_once_with()
        
        
