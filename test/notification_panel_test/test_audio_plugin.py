import unittest
import alsaaudio
from mock import Mock

from notification_panel.audio_plugin import AudioSettingsPlugin

class AudioSettingsPluginTestCase(unittest.TestCase):
    
    NO_AUDIO_CARD = []
    MOCK_AUDIO_CARD = ['mock audio card']
    MASTER_MIXER = 'Master'
    VOLUME_MUTED = 0
    VOLUME_LOW = AudioSettingsPlugin.VOLUME_THRESH_LOW - 1
    VOLUME_MED = AudioSettingsPlugin.VOLUME_THRESH_LOW + 1
    VOLUME_HIGH = AudioSettingsPlugin.VOLUME_THRESH_HIGH + 1
    
    def test_audio_plugin_disabled_if_no_card_has_master_mixer(self):
        alsaaudio.cards = Mock(return_value = ['mock_card_1', 'mock_card_2'])
        values = {0: 'mock_mixer_1', 1: 'mock_mixer_2'}
        alsaaudio.mixers = Mock(side_effect = lambda cardindex: values[cardindex])
        
        self.assertFalse(AudioSettingsPlugin.is_plugin_enabled())
        
    def test_audio_plugin_enabled_if_second_card_has_master_mixer(self):
        alsaaudio.cards = Mock(return_value = ['mock_card_1', 'mock_card_2'])
        values = {0: 'mock_mixer_1', 1: self.MASTER_MIXER}
        alsaaudio.mixers = Mock(side_effect = lambda cardindex: values[cardindex])
        
        self.assertTrue(AudioSettingsPlugin.is_plugin_enabled())
        self.assertTrue(AudioSettingsPlugin.card_index == 1)
        
    # Note: we are testing logic that is called from the audio plugin constructor,
    # so we have to construct an audio plugin object for each test

    def test_audio_plugin_displays_no_icon_if_disabled(self):
        alsaaudio.cards = Mock(return_value = self.NO_AUDIO_CARD)
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self.assertFalse(self._audio_plugin._set_index.called)
    
    def test_audio_plugin_launches_settings_when_clicked(self):
        alsaaudio.cards = Mock(return_value = self.MOCK_AUDIO_CARD)
        alsaaudio.mixers = Mock(return_value = self.MASTER_MIXER)
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self.assertEqual('gnome-control-center --class=eos-audio-manager sound', self._audio_plugin.get_launch_command())

    def test_audio_plugin_displays_muted_icon(self):
        alsaaudio.cards = Mock(return_value = self.MOCK_AUDIO_CARD)
        alsaaudio.mixers = Mock(return_value = self.MASTER_MIXER)
        alsaaudio.Mixer = Mock(return_value = MockMixer(volume = self.VOLUME_MUTED))
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self._audio_plugin._set_index.assert_called_once_with(AudioSettingsPlugin.VOLUME_MUTED)
         
    def test_audio_plugin_displays_low_icon(self):
        alsaaudio.cards = Mock(return_value = self.MOCK_AUDIO_CARD)
        alsaaudio.mixers = Mock(return_value = self.MASTER_MIXER)
        alsaaudio.Mixer = Mock(return_value = MockMixer(volume = self.VOLUME_LOW))
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self._audio_plugin._set_index.assert_called_once_with(AudioSettingsPlugin.VOLUME_LOW)

    def test_audio_plugin_displays_med_icon(self):
        alsaaudio.cards = Mock(return_value = self.MOCK_AUDIO_CARD)
        alsaaudio.mixers = Mock(return_value = self.MASTER_MIXER)
        alsaaudio.Mixer = Mock(return_value = MockMixer(volume = self.VOLUME_MED))
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self._audio_plugin._set_index.assert_called_once_with(AudioSettingsPlugin.VOLUME_MED)
    
    def test_audio_plugin_displays_high_icon(self):
        alsaaudio.cards = Mock(return_value = self.MOCK_AUDIO_CARD)
        alsaaudio.mixers = Mock(return_value = self.MASTER_MIXER)
        alsaaudio.Mixer = Mock(return_value = MockMixer(volume = self.VOLUME_HIGH))
        self._audio_plugin = MockAudioSettingsPlugin(1)
        self._audio_plugin._set_index.assert_called_once_with(AudioSettingsPlugin.VOLUME_HIGH)

class MockAudioSettingsPlugin(AudioSettingsPlugin):
    
    def __init__(self, size):
        self._set_index = Mock()
        super(MockAudioSettingsPlugin, self).__init__(size)
    
    def _init_thread(self):
        pass
        
class MockMixer:
    
    def __init__(self, volume):
        self._volume = volume
        
    def getmute(self):
        if self._volume == 0:
            mute = [1L]
        else:
            mute = [0L]
        return mute
        
    def getvolume(self):
        return [self._volume]
