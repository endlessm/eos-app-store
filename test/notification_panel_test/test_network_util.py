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
        
        
        
        