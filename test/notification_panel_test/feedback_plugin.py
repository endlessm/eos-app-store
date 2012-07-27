import unittest
from mock import Mock

from notification_panel.feedback_plugin import FeedbackPlugin

class FeedbackPluginTestCase(unittest.TestCase):
    def test_feeback_has_no_launch_command(self):
        self.assertEqual('gnome-control-center --class=eos-network-manager network', FeedbackPlugin.get_launch_command())

