import unittest
from mock import Mock

from notification_panel.battery_plugin import BatteryPlugin
from util.dbus_utils import DbusUtils

class BatteryPluginTestCase(unittest.TestCase):
    
    def test_battery_plugin_disabled_if_no_battery_present(self):
        DbusUtils.has_device_of_type = Mock(return_value = False)
        
        self.assertFalse(BatteryPlugin.is_plugin_enabled())
        
    def test_battery_plugin_enabled_if_battery_present(self):
        DbusUtils.has_device_of_type = Mock(return_value = True)
        
        self.assertTrue(BatteryPlugin.is_plugin_enabled())

    def test_execute_calls_display_menu(self):
        test_object = BatteryPlugin(22)
        
        test_object._presenter = Mock()
        test_object._presenter.display_menu = Mock()
        
        test_object.execute()
        
        test_object._presenter.display_menu.assert_called_once_with()
        
        