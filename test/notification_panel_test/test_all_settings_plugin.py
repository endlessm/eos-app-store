import unittest
from mock import Mock, patch

from notification_panel.all_settings_plugin import AllSettingsPlugin
from osapps.app_launcher import AppLauncher
from desktop.endless_desktop_view import EndlessDesktopView
from desktop.background_chooser import BackgroundChooser

class AllSettingsPluginTestCase(unittest.TestCase):
    def test_settings_does_not_directly_launch_command(self):
        self.assertIsNone(AllSettingsPlugin(1).get_launch_command())
        
    def test_settings_update(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._update_software(Mock(), Mock())
        AppLauncher.launch.assert_called_once_with('sudo apt-get update; sudo apt-get upgrade -y')

    def test_settings_settings(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._launch_settings(Mock(), Mock())
        AppLauncher.launch.assert_called_once_with('sudo gnome-control-center --class=eos-network-manager')

    @patch('desktop.background_chooser.BackgroundChooser.__init__', Mock(return_value=None))
    def test_settings_desktop(self):
        view = Mock()
        AllSettingsPlugin.get_toplevel = Mock(return_value=view)
        background_chooser = BackgroundChooser(view)
        plugin = AllSettingsPlugin(1)
        plugin._desktop_background(Mock(), Mock())
        background_chooser.__init__.assert_called_once_with(view)

    def test_settings_logout(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._logout(Mock(), Mock())
        AppLauncher.launch.assert_called_once_with('kill -9 -1')

    def test_settings_restart(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._restart(Mock(), Mock())
        AppLauncher.launch.assert_called_once_with('sudo shutdown -r now')

    def test_settings_shutdown(self):
        AppLauncher.launch = Mock()
        plugin = AllSettingsPlugin(1)
        plugin._confirm = Mock(return_value = True)
        plugin._shutdown(Mock(), Mock())
        AppLauncher.launch.assert_called_once_with('sudo shutdown -h now')
