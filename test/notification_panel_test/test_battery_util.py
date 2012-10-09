import unittest
import uuid

from mock import Mock, MagicMock, call
from notification_panel.battery_util import BatteryUtil

class TestBatteryUtilTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_dbus = Mock()
        mock_system_bus = Mock()
        self._mock_hal_manager_object = Mock()
        self._hal_manager_interface = Mock()
        self._mock_battery_object = Mock()

        self._mock_dbus.SystemBus = Mock(return_value=mock_system_bus)
        mock_system_bus.get_object = Mock(side_effect = self.mock_get_object)

        self._mock_dbus.Interface = Mock(side_effect=self.mock_interface_call)
        
    def test_dbus_returns_battery_percentage_if_battery_is_present(self):
        expected_battery_level = str(uuid.uuid1())
        self._primary_battery_device = Mock()

        self._hal_manager_interface.FindDeviceByCapability = HALInterface([self._primary_battery_device])
        
        self._battery_interface = Mock()
        self._battery_interface.GetProperty = Mock(return_value=expected_battery_level)
        
        actual_battery_level = BatteryUtil.get_battery_level(self._mock_dbus)
        
        self._battery_interface.GetProperty.assert_called_once_with('battery.charge_level.percentage')
        self.assertEquals(expected_battery_level, actual_battery_level)
    
        
    def test_dbus_returns_none_if_battery_is_not_present(self):
        self._hal_manager_interface.FindDeviceByCapability = HALInterface([])
        
        actual_battery_level = BatteryUtil.get_battery_level(self._mock_dbus)
        
        self.assertIsNone(actual_battery_level)    
    
    def mock_interface_call(self, interface_property, manager_path):
        if interface_property == self._mock_hal_manager_object and manager_path == BatteryUtil.HAL_DBUS_MANAGER_PATH:
            return self._hal_manager_interface
        if interface_property == self._mock_battery_object and manager_path == BatteryUtil.HAL_DBUS_DEVICE_PATH:
            return self._battery_interface
        
    def mock_get_object(self, path, uri):
        if path == BatteryUtil.HAL_DBUS_PATH and uri == BatteryUtil.HAL_DBUS_MANAGER_URI:
            return self._mock_hal_manager_object
        if path == BatteryUtil.HAL_DBUS_PATH and uri == self._primary_battery_device:
            return self._mock_battery_object 
             
        
class HALInterface(): 
    def __init__(self, batteries):
        self._batteries = batteries
        
    def __call__(self, *args, **kwargs):
        kwarg_one = kwargs['dbus_interface']
        
        if args[0] == 'battery' and len(args) == 1 and kwarg_one == BatteryUtil.HAL_DBUS_MANAGER_PATH and len(kwargs) == 1:
            return self._batteries
    
    
     