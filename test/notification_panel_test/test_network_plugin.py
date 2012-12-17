import unittest
from notification_panel.network_plugin import NetworkSettingsPlugin

class NetworkPluginTestCase(unittest.TestCase):
    def test_execute_calls_display_menu(self):
        test_object = NetworkSettingsPlugin(22)
        self.assertEqual('sudo gnome-control-center network', test_object.get_launch_command())

