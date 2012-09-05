import unittest
from mock import Mock

from notification_panel.audio_plugin import AudioSettingsPlugin

class AudioSettingsPluginTestCase(unittest.TestCase):
    def test_audio_plugin_launches_settings_when_clicked(self):
        self.assertEqual('sudo gnome-control-center --class=eos-audio-manager sound', AudioSettingsPlugin(1).get_launch_command())
