import unittest

from notification_panel.all_settings_plugin import AllSettingsPlugin

class AllSettingsPluginTestCase(unittest.TestCase):
    def test_settings_opens_the_main_settings(self):
        self.assertEqual('sudo gnome-control-center --class=eos-network-manager', AllSettingsPlugin(1).get_launch_command())

