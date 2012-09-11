import unittest
from mock import Mock

from notification_panel.audio_plugin import AudioSettingsPlugin
import sys

class AudioSettingsPluginTestCase(unittest.TestCase):
    def test_audio_plugin_launches_settings_when_clicked(self):
        self.assertEqual('sudo gnome-control-center --class=eos-audio-manager sound', MockAudioSettingsPlugin(1).get_launch_command())

class MockAudioSettingsPlugin (AudioSettingsPlugin):
    
    def init(self, size):
        super(AudioSettingsPlugin, self).__init__(size)
    
    def _init_thread(self):
        pass
    
    def _get_volume(self):
        pass
    