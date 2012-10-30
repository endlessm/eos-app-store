import unittest
import uuid

from mock import Mock, MagicMock, call
from notification_panel.battery_provider import BatteryProvider

class TestBatteryUtilTestCase(unittest.TestCase):
    def setUp(self):
        self._expected_battery_level = str(uuid.uuid1())
        self._is_charging = 0
        self._time_to_depletion = 1232
        
        self._mock_dbus = Mock()
        self._mock_dbus_utils = Mock()
        mock_system_bus = Mock()
        
        self._mock_hal_manager_object = Mock()
        self._hal_manager_interface = Mock()
        
        self._battery_interface = Mock()
        self._battery_interface.GetProperty = Mock(side_effect=self.mock_get_battery_property)
        self._battery_interface.connect_to_signal = Mock(return_value=None)

        self._ac_adapter_interface = Mock()
        self._ac_adapter_interface.GetProperty = Mock(side_effect=self.mock_get_ac_adapter_property)
        self._ac_adapter_interface.connect_to_signal = Mock(return_value=None)
        self._mock_battery_object = Mock()
        
        self._mock_ac_adapter_object = Mock()

        self._mock_dbus_utils.get_system_bus = Mock(return_value=mock_system_bus)
        mock_system_bus.get_object = Mock(side_effect = self.mock_get_object)

        self._mock_dbus.Interface = Mock(side_effect=self.mock_interface_call)
        self.test_object = BatteryProvider(self._mock_dbus, self._mock_dbus_utils)
        
    def _callback_func(self, battery):
        self._battery_info = battery
        
    def test_after_registering_listener_battery_info_is_returned(self):
        self._primary_battery_device = Mock()
        self._ac_adapter_device = Mock()
        self._hal_manager_interface.FindDeviceByCapability = HALInterface([self._primary_battery_device], [self._ac_adapter_device])
        
        self.test_object.add_battery_callback(self._callback_func)
        
        self.assertEquals(self._expected_battery_level, self._battery_info.level())
        self.assertEquals(self._time_to_depletion, self._battery_info.time_to_depletion())
        self.assertEquals(self._is_charging, self._battery_info.charging())
        
    def test_dbus_returns_none_if_battery_is_not_present(self):
        self._ac_adapter_device = Mock()
        self._hal_manager_interface.FindDeviceByCapability = HALInterface([], [self._ac_adapter_device])
        
        self.test_object.add_battery_callback(self._callback_func)
        
        self.assertIsNone(self._battery_info.level())
        self.assertIsNone(self._battery_info.time_to_depletion())
        
    def test_is_recharging_returns_true_if_charging(self):
        self._is_charging = 1
        self._primary_battery_device = Mock()
        self._ac_adapter_device = Mock()
        self._hal_manager_interface.FindDeviceByCapability = HALInterface([self._primary_battery_device], [self._ac_adapter_device])
        
        self.test_object.add_battery_callback(self._callback_func)
        
        self.assertEquals(self._expected_battery_level, self._battery_info.level())
        self.assertEquals(self._time_to_depletion, self._battery_info.time_to_depletion())
        self.assertEquals(self._is_charging, self._battery_info.charging())
    

    def test_if_exceptions_occur_we_return_nulls(self):
        self._primary_battery_device = Mock()
        self._ac_adapter_device = Mock()
        self._hal_manager_interface.FindDeviceByCapability = HALInterface([self._primary_battery_device], [self._ac_adapter_device])
        self._battery_interface = Mock()
        self._battery_interface.GetProperty = Mock(side_effect=Exception())
        
        self.test_object.add_battery_callback(self._callback_func)
        
        self.assertEquals(self._expected_battery_level, self._battery_info.level())
        self.assertEquals(self._time_to_depletion, self._battery_info.time_to_depletion())
        self.assertEquals(self._is_charging, self._battery_info.charging())
        
        self.assertIsNone(self._battery_info.level())    
        self.assertIsNone(self._battery_info.charging()) 
        
    def mock_interface_call(self, interface_property, manager_path):
        if interface_property == self._mock_hal_manager_object and manager_path == BatteryProvider.HAL_DBUS_MANAGER_PATH:
            return self._hal_manager_interface
        if interface_property == self._mock_battery_object and manager_path == BatteryProvider.HAL_DBUS_DEVICE_PATH:
            return self._battery_interface
        if interface_property == self._mock_ac_adapter_object and manager_path == BatteryProvider.HAL_DBUS_DEVICE_PATH:
            return self._ac_adapter_interface
        
    def mock_get_object(self, path, uri):
        if path == BatteryProvider.HAL_DBUS_PATH and uri == BatteryProvider.HAL_DBUS_MANAGER_URI:
            return self._mock_hal_manager_object
        if path == BatteryProvider.HAL_DBUS_PATH and uri == self._primary_battery_device:
            return self._mock_battery_object 
        if path == BatteryProvider.HAL_DBUS_PATH and uri == self._ac_adapter_device:
            return self._mock_ac_adapter_object 

    def mock_get_battery_property(self, battery_property):
        if battery_property == BatteryProvider.BATTERY_PERCENTAGE_PROPERTY:
            return self._expected_battery_level
        if battery_property == BatteryProvider.BATTERY_REMAINING_TIME_PROPERTY:
            return self._time_to_depletion
        
    def mock_get_ac_adapter_property(self, ac_adapter_property):
        if ac_adapter_property == BatteryProvider.AC_ADAPTER_PRESENT:
            return self._is_charging
    
class HALInterface(): 
    def __init__(self, batteries, ac_adapter):
        self._batteries = batteries
        self._ac_adapter = ac_adapter
        
    def __call__(self, *args, **kwargs):
        kwarg_one = kwargs['dbus_interface']
        if len(args) == 1 and kwarg_one == BatteryProvider.HAL_DBUS_MANAGER_PATH and len(kwargs) == 1:
            if args[0] == 'battery':
                return self._batteries
            elif args[0] == 'ac_adapter':
                return self._ac_adapter
