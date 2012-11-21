import unittest
from mock import Mock

from notification_panel.network_plugin import NetworkSettingsPlugin

class NetworkPluginTestCase(unittest.TestCase):
    def test_initially_shortcut_list_is_retrieved_from_app_util_manager(self):
        self.assertEqual('sudo gnome-control-center network', MockNetworkSettingsPlugin(1).get_launch_command())
        
class MockNetworkSettingsPlugin (NetworkSettingsPlugin):
    def _start_thread(self):
        pass    