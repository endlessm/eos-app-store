import unittest
from mock import Mock

from notification_panel.time_display_plugin import TimeDisplayPlugin

class TimePluginTestCase(unittest.TestCase):
    def test_time_plugin_launches_time_when_clicked(self):
        self.assertEqual('sudo gnome-control-center --class=eos-network-manager datetime', TimeDisplayPlugin(1).get_launch_command())

