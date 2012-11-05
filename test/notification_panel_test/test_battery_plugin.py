import unittest
from mock import Mock

from notification_panel.battery_plugin import BatteryPlugin

class BatteryPluginTestCase(unittest.TestCase):
    def test_execute_calls_display_menu(self):
        test_object = BatteryPlugin(22)
        
        test_object._presenter = Mock()
        test_object._presenter.display_menu = Mock()
        
        test_object.execute()
        
        test_object._presenter.display_menu.assert_called_once_with()
        
        