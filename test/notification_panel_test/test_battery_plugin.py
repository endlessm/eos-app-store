import unittest
from mock import Mock

from notification_panel.battery_plugin import BatteryPlugin

class BatteryPluginTestCase(unittest.TestCase):
    def setUp(self):
        self.battery_provider = Mock()
        self.battery_info = Mock()
        self.battery_provider.get_battery_info = Mock(return_value=self.battery_info)
    
    def test_battery_plugin_disabled_if_no_battery_present(self):
        self.battery_info.level = Mock(return_value=None)

        self.assertFalse(BatteryPlugin.is_plugin_enabled(self.battery_provider))
        
    def test_battery_plugin_enabled_if_battery_present(self):
        self.battery_info.level = Mock(return_value="yeah!")
        
        self.assertTrue(BatteryPlugin.is_plugin_enabled(self.battery_provider))

    def test_execute_calls_display_menu(self):
        test_object = BatteryPlugin(22)
        
        test_object._presenter = Mock()
        test_object._presenter.display_menu = Mock()
        
        test_object.execute()
        
        test_object._presenter.display_menu.assert_called_once_with()
        
        
