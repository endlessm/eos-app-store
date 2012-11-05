import unittest
from mock import Mock

from util.dbus_utils import DbusUtils

class DbusUtilsTestCase(unittest.TestCase):
    
    # Note: to simulate a static system bus, need to define it
    # outside of setUp (which is called for each test)
    _mock_system_bus = Mock()
    
    def setUp(self):
        self._mock_data_bus = Mock()
        self._mock_data_bus.SystemBus = Mock(return_value=self._mock_system_bus)
        self._test_object = DbusUtils(self._mock_data_bus)

        self._mock_hal_manager = Mock()
        self._mock_system_bus.get_object = Mock(return_value = self._mock_hal_manager)
        self._mock_hal_manager_interface = Mock()
        self._mock_device_type = Mock()

        self._mock_device = Mock()

        self._mock_device_object = Mock()
        def get_object(path, device):
            if path == DbusUtils.HAL_DBUS_PATH and device == DbusUtils.HAL_DBUS_MANAGER_URI:
                return self._mock_hal_manager
            elif path == DbusUtils.HAL_DBUS_PATH and device == self._mock_device:
                return self._mock_device_object
        self._mock_system_bus.get_object = get_object
        
        self._mock_device_interface = Mock()
        def get_interface(device_object, device_path):
            if device_object == self._mock_hal_manager and device_path == DbusUtils.HAL_DBUS_MANAGER_PATH:
                return self._mock_hal_manager_interface
            elif device_object == self._mock_device_object and device_path == DbusUtils.HAL_DBUS_DEVICE_PATH:
                return self._mock_device_interface
        self._mock_data_bus.Interface = get_interface
        
    def test_get_system_bus_always_returns_static_system_bus(self):
        self._mock_data_bus.SystemBus = Mock(return_value=None)
        
        self.assertEquals(self._test_object.get_system_bus(), self._mock_system_bus)
        self.assertEquals(DbusUtils(self._mock_data_bus).get_system_bus(), self._mock_system_bus)
        self.assertEquals(DbusUtils(self._mock_data_bus).get_system_bus(), self._mock_system_bus)

    # TODO test reg prop listener 
    
    def test_add_signal_callback_adds_signal_receiver_to_bus(self):
        def mock_add_signal_receiver(callback_wrapper, dbus_interface):
            self._callback_wrapper = callback_wrapper
            self._dbus_interface = dbus_interface
            
        self._mock_system_bus.add_signal_receiver = mock_add_signal_receiver
        regex_match = r'.*battery.*'
        callback_function = Mock()
        self._test_object.add_signal_callback(regex_match, callback_function)

        self.assertEquals(self._dbus_interface, DbusUtils.HAL_DBUS_MANAGER_PATH)        
        
        self._callback_wrapper('test_string')
        self._callback_wrapper('any_battery_string')
        callback_function.assert_called_once_with()

    def test_has_device_of_type_returns_false_if_no_matching_device(self):
        mock_devices = []
        self._mock_hal_manager_interface.FindDeviceByCapability = Mock(return_value = mock_devices)
        self._mock_data_bus.Interface = Mock(return_value = self._mock_hal_manager_interface)

        self.assertFalse(self._test_object.has_device_of_type(self._mock_device_type))
        self._mock_data_bus.Interface.assert_called_once_with(self._mock_hal_manager, DbusUtils.HAL_DBUS_MANAGER_PATH)
        self._mock_hal_manager_interface.FindDeviceByCapability.assert_called_once_with(self._mock_device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)
        
    def test_has_device_of_type_returns_false_if_one_matching_device(self):
        mock_devices = [self._mock_device]
        self._mock_hal_manager_interface.FindDeviceByCapability = Mock(return_value = mock_devices)
        self._mock_data_bus.Interface = Mock(return_value = self._mock_hal_manager_interface)

        self.assertTrue(self._test_object.has_device_of_type(self._mock_device_type))
        self._mock_data_bus.Interface.assert_called_once_with(self._mock_hal_manager, DbusUtils.HAL_DBUS_MANAGER_PATH)
        self._mock_hal_manager_interface.FindDeviceByCapability.assert_called_once_with(self._mock_device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)

    #TODO test get_device_property
    
    def test_get_device_interface_returns_none_if_no_matching_device(self):
        mock_devices = []
        self._mock_hal_manager_interface.FindDeviceByCapability = Mock(return_value = mock_devices)
        self._mock_data_bus.Interface = Mock(return_value = self._mock_hal_manager_interface)
        
        self.assertIsNone(self._test_object.get_device_interface(self._mock_device_type))
        self._mock_data_bus.Interface.assert_called_once_with(self._mock_hal_manager, DbusUtils.HAL_DBUS_MANAGER_PATH)
        self._mock_hal_manager_interface.FindDeviceByCapability.assert_called_once_with(self._mock_device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)

    def test_get_device_interface_returns_interface_if_one_matching_device(self):
        mock_devices = [self._mock_device]
        self._mock_hal_manager_interface.FindDeviceByCapability = Mock(return_value = mock_devices)
        
        self.assertEquals(self._test_object.get_device_interface(self._mock_device_type), self._mock_device_interface)
        self._mock_hal_manager_interface.FindDeviceByCapability.assert_called_once_with(self._mock_device_type, dbus_interface=DbusUtils.HAL_DBUS_MANAGER_PATH)
        