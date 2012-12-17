import unittest
from mock import Mock, MagicMock, call
from notification_panel.network_util import NetworkUtil


class NetworkUtilTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_dbus_utils = Mock()
        self._mock_system_bus = Mock()
        self._mock_system_bus_object = Mock()
        self._mock_access_point_object = Mock()
        self._mock_data_bus = Mock()
        
        self._mock_dbus_utils.get_data_bus = Mock(return_value = self._mock_data_bus)
        self._mock_system_bus.get_object = MagicMock(side_effect=[self._mock_system_bus_object, self._mock_access_point_object])
        self._mock_dbus_utils.get_system_bus = Mock(return_value = self._mock_system_bus)
        
        self._test_object = NetworkUtil(self._mock_dbus_utils)

    def test_register_device_listener_change_listener_connects_to_property_changed_signal(self):
        mock_callback = Mock()
        
        self._test_object.register_device_change_listener(mock_callback)
        
        self._mock_system_bus.get_object.assert_called_once_with(NetworkUtil.DBUS_NETWORK_MANAGER_PATH, NetworkUtil.DBUS_NETWORK_MANAGER_URI)
        self._mock_system_bus_object.connect_to_signal.assert_called_once_with(NetworkUtil.DBUS_PROPERTY_CHANGED_SIGNAL, mock_callback)
        self._mock_dbus_utils.get_system_bus.assert_called_once_with()
        
    def test_get_network_state_returns_true_if_wireless_device(self):
        mock_interface = Mock()
        mock_devices = [Mock()]
        mock_active_ap = Mock()
        mock_level = 70
        
        mock_device_properties = {NetworkUtil.NETWORK_DEVICE_TYPE: NetworkUtil.WIRELESS_DEVICE, NetworkUtil.NETWORK_DEVICE_STATE: NetworkUtil.DEVICE_CONNECTED}
        mock_wireless_properties = {NetworkUtil.ACTIVE_WIRELESS_PROPERTY_KEY: mock_active_ap}
        
        mock_ap_properties = {NetworkUtil.AP_CONNECTION_STRENGTH: mock_level}

        self._mock_access_point_object.GetAll = Mock(return_value = mock_ap_properties)
        
        mock_interface.GetDevices = Mock(return_value = mock_devices)
        mock_interface.GetAll = MagicMock(side_effect=[mock_device_properties, mock_wireless_properties, mock_ap_properties])
        
        self._mock_data_bus.Interface = Mock(return_value = mock_interface)
        
        actual_state = self._test_object.get_network_state()
        self.assertEqual(mock_level, actual_state)
        
        call1 = call(self._mock_system_bus_object, NetworkUtil.DBUS_NETWORK_MANAGER_PATH)
        call2 = call(self._mock_system_bus_object, NetworkUtil.DBUS_PROPERTIES_PATH)
        self._mock_data_bus.Interface.assert_has_calls([call1,call2])
        
        
        
        