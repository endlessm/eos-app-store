import unittest
from mock import Mock

from notification_panel.battery_model import BatteryModel
from notification_panel.battery_provider import Battery

class BatteryModelTestCase(unittest.TestCase):
    def test_when_button_is_clicked_power_settings_are_opened(self):
        mock_battery_provider = Mock()
        mock_app_launcher= Mock()

        test_object = BatteryModel(mock_battery_provider, mock_app_launcher)
        test_object.open_settings()

        mock_app_launcher.launch.assert_called_once_with(BatteryModel.SETTINGS_COMMAND) 
    
    def test_level_returns_battery_level_from_battery(self):
        battery = Mock()
        battery.level = Mock(return_value=86) 
        
        mock_battery_provider = Mock()
        mock_battery_provider.get_battery = Mock(return_value=battery)

        test_object = BatteryModel(mock_battery_provider)

        self.assertEquals(86, test_object.level())
        
    def test_time_to_depletion_returns_depletion_time_as_string_from_battery(self):
        battery = Mock()
        battery.time_to_depletion = Mock(return_value=1800) 
        
        mock_battery_provider = Mock()
        mock_battery_provider.get_battery = Mock(return_value=battery)

        test_object = BatteryModel(mock_battery_provider)

        self.assertEquals('0:30', test_object.time_to_depletion()) 

