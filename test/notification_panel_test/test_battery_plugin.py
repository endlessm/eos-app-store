import unittest

from notification_panel.battery_plugin import BatteryPlugin

class BatteryPluginTestCase(unittest.TestCase):
    def test_launch_command_is_power_settings(self):
        self.assertEqual('gksudo gnome-control-center power', BatteryPlugin(1).get_launch_command())
