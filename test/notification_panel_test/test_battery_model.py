import unittest
from mock import Mock

from notification_panel.battery_model import BatteryModel
from notification_panel.battery_provider import Battery

class BatteryModelTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_battery_provider = Mock()
        self._mock_battery_provider.add_battery_callback = self._add_battery_callback
        
        
    def test_when_button_is_clicked_power_settings_are_opened(self):
        mock_app_launcher= Mock()

        test_object = BatteryModel(self._mock_battery_provider, mock_app_launcher)
        test_object.open_settings()

        mock_app_launcher.launch.assert_called_once_with(BatteryModel.SETTINGS_COMMAND) 
    
    def test_model_is_a_passthrough_for_battery_change_events(self):
        mock_app_launcher= Mock()

        test_object = BatteryModel(self._mock_battery_provider, mock_app_launcher)
    
        invoked_callback = Mock(return_value=None)
        
        test_object.add_listener(BatteryModel.BATTERY_STATE_CHANGED, invoked_callback)
        battery = Mock()
        battery.level = Mock(return_value=75) 
    
        self._registered_callback(battery)
        
        self.assertTrue(invoked_callback.called)
        
    def test_level_returns_battery_level_from_battery(self):
        battery = Mock()
        battery.level = Mock(return_value=86) 

        test_object = BatteryModel(self._mock_battery_provider)
        
        self._registered_callback(battery)

        self.assertEquals(86, test_object.level())
        
    def test_time_to_depletion_returns_depletion_time_as_string_from_battery(self):
        battery = Mock()
        battery.time_to_depletion = Mock(return_value=1800) 
        
        test_object = BatteryModel(self._mock_battery_provider)
        self._registered_callback(battery)
        
        self.assertEquals('0:30', test_object.time_to_depletion()) 
        
    def _add_battery_callback(self, callback):
        self._registered_callback = callback

