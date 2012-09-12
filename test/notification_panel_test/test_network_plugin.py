import unittest
from mock import Mock

from notification_panel.network_plugin import NetworkSettingsPlugin

class NetworkPluginTestCase(unittest.TestCase):
    def test_initially_shortcut_list_is_retrieved_from_app_util_manager(self):
        self.assertEqual('sudo gnome-control-center --class=eos-network-manager network', NetworkSettingsPlugin(1).get_launch_command())
    


