import unittest
import uuid

from mock import Mock, MagicMock, call
from notification_panel.battery_provider import BatteryProvider

class TestBatteryUtilTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_level = Mock()
        self._mock_time_left = Mock()
        self._mock_charging = Mock()
        
        self._mock_dbus_utils = Mock()
        self._mock_dbus_utils.get_device_property = self._mock_get_device_property
        self._test_object = BatteryProvider(self._mock_dbus_utils)
        
    def test_add_battery_callback_registers_correct_adapter_battery_and_device_callbacks(self):
        def callback_function(battery):
            self._battery_info = battery
        
        self._test_object.add_battery_callback(callback_function)
        
        self._mock_dbus_utils.register_property_listener.assert_has_calls([call(self._test_object.BATTERY_TYPE, self._test_object._battery_modified),
                                                                       call(self._test_object.AC_ADAPTER_TYPE, self._test_object._battery_modified),
                                                                       ])
        
        self._mock_dbus_utils.add_signal_callback.assert_called_with(r'.*battery.*', self._test_object._devices_changed)
        
        # Make sure that the property callback is correct
        self._mock_level = Mock()
        self._mock_time_left = Mock()
        self._mock_charging = Mock()
        
        self._test_object._battery_modified(0, None)
        
        self.assertEquals(self._mock_time_left, self._battery_info.time_to_depletion())
        self.assertEquals(self._mock_level, self._battery_info.level())
        self.assertEquals(self._mock_charging, self._battery_info.charging())
        
        # Make sure that the device changed callback is correct
        self._mock_level = Mock()
        self._mock_time_left = Mock()
        self._mock_charging = Mock()
        
        self._test_object._devices_changed()
        
        self.assertEquals(self._mock_time_left, self._battery_info.time_to_depletion())
        self.assertEquals(self._mock_level, self._battery_info.level())
        self.assertEquals(self._mock_charging, self._battery_info.charging())
        
    def test_add_battery_callback_gets_battery_status_updated(self):
        def callback_function(battery):
            self._battery_info = battery
        
        self._test_object.add_battery_callback(callback_function)
        
        self.assertEquals(self._mock_time_left, self._battery_info.time_to_depletion())
        self.assertEquals(self._mock_level, self._battery_info.level())
        self.assertEquals(self._mock_charging, self._battery_info.charging())
        
    def test_if_add_battery_callback_fails_to_register_listeners_dont_throw_exceptions(self):
        def callback_function(battery):
            self._battery_info = battery

        self._mock_dbus_utils.register_property_listener = Mock(side_effect=Exception())
        self._test_object.add_battery_callback(callback_function)
        
        self.assertEquals(self._mock_time_left, self._battery_info.time_to_depletion())
        self.assertEquals(self._mock_level, self._battery_info.level())
        self.assertEquals(self._mock_charging, self._battery_info.charging())
        
    def test_get_battery_info_returns_values_from_dbus(self):
        self._battery_info = self._test_object.get_battery_info()
        
        self.assertEquals(self._mock_time_left, self._battery_info.time_to_depletion())
        self.assertEquals(self._mock_level, self._battery_info.level())
        self.assertEquals(self._mock_charging, self._battery_info.charging())
        
    def test_get_battery_info_returns_no_battery_if_exception_gets_thrown(self):
        self._mock_dbus_utils.get_device_property = Mock(side_effect=Exception())

        self._battery_info = self._test_object.get_battery_info()
        
        self.assertIsNone(self._battery_info.time_to_depletion())
        self.assertIsNone(self._battery_info.level())
        self.assertIsNone(self._battery_info.charging())
        
    def test_get_battery_info_returns_no_battery_if_we_have_no_batteries(self):
        self._mock_dbus_utils.has_device_of_type = Mock(return_value=False)

        self._battery_info = self._test_object.get_battery_info()
        
        self.assertIsNone(self._battery_info.time_to_depletion())
        self.assertIsNone(self._battery_info.level())
        self.assertIsNone(self._battery_info.charging())
    
    def _mock_get_device_property(self, device, property_name):
        if device == BatteryProvider.BATTERY_TYPE and property_name == BatteryProvider.BATTERY_REMAINING_TIME_PROPERTY:
            return self._mock_time_left
        elif device == BatteryProvider.BATTERY_TYPE and property_name == BatteryProvider.BATTERY_PERCENTAGE_PROPERTY:
            return self._mock_level
        elif device == BatteryProvider.AC_ADAPTER_TYPE and property_name == BatteryProvider.AC_ADAPTER_PRESENT_PROPERTY:
            return self._mock_charging
