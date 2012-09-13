import unittest
from mock import Mock

from notification_panel.all_settings_plugin import AllSettingsPlugin
from osapps.app_launcher import AppLauncher

class AllSettingsPluginTestCase(unittest.TestCase):
    def test_settings_does_not_directly_launch_command(self):
        self.assertIsNone(AllSettingsPlugin(1).get_launch_command())
        
    def test_settings_settings(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._button_settings.emit('button-press-event', None)
        AppLauncher.launch.assert_called_once_with('sudo gnome-control-center --class=eos-network-manager')

    def test_settings_logout(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._button_logout.emit('button-press-event', None)
        AppLauncher.launch.assert_called_once_with('kill -9 -1')

    def test_settings_restart(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._button_restart.emit('button-press-event', None)
        AppLauncher.launch.assert_called_once_with('sudo shutdown -r now')

    def test_settings_shutdown(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._button_shutdown.emit('button-press-event', None)
        AppLauncher.launch.assert_called_once_with('sudo shutdown -h now')
