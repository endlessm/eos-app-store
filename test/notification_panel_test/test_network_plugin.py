import unittest
from mock import Mock
from notification_panel.network_plugin import NetworkSettingsPlugin

class NetworkPluginTestCase(unittest.TestCase):
    def test_execute_calls_display_menu(self):
        NetworkSettingsPlugin._create_mvp = Mock(return_value=None)
        icon_size = Mock()
        test_object = NetworkSettingsPlugin(icon_size)
        self.assertEqual('sudo gnome-control-center network', test_object.get_launch_command())
        test_object._create_mvp.assert_called_once_with(icon_size)

