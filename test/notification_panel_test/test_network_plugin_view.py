import unittest
from mock import Mock
from notification_panel.network_plugin_view import NetworkPluginView

class NetworkPluginViewTestCase(unittest.TestCase):
    def test_clicking_network_icon_opens_network_settings(self):
        self.assertEqual('sudo gnome-control-center network', NetworkPluginView(Mock(), 1).get_launch_command())