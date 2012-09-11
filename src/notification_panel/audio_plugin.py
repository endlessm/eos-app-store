import threading
import alsaaudio
import time

from icon_plugin import IconPlugin

class AudioSettingsPlugin(IconPlugin, threading.Thread):
    COMMAND = 'sudo gnome-control-center --class=eos-audio-manager sound'
    ICON_NAMES = ['audio-volume-muted.png',
                  'audio-volume-low.png',
                  'audio-volume-medium.png',
                  'audio-volume-high.png']

    VOLUME_MUTED = 0
    VOLUME_LOW = 1
    VOLUME_MED = 2
    VOLUME_HIGH = 3
    
    VOLUME_THRESH_LOW = 55
    VOLUME_THRESH_HIGH = 85
    
    def __init__(self, icon_size):
        # Only display the audio settings if a sound card is installed
        if AudioSettingsPlugin.is_plugin_enabled():
            self._volume = self._get_volume()
            super(AudioSettingsPlugin, self).__init__(icon_size, self.ICON_NAMES, self.COMMAND, self._volume)
            self._init_thread()

    @staticmethod
    def is_plugin_enabled():
        sound_cards = alsaaudio.cards()
        return len(sound_cards) > 0
        
    def _init_thread(self):
        threading.Thread.__init__(self)
        self.start()
        
    def _get_volume(self):
        master = alsaaudio.Mixer()
        mute = min(master.getmute())
        if mute > 0:
            level = self.VOLUME_MUTED
        else:
            volume = max(master.getvolume())
            if volume < self.VOLUME_THRESH_LOW:
                level = self.VOLUME_LOW
            elif volume < self.VOLUME_THRESH_HIGH:
                level = self.VOLUME_MED
            else:
                level = self.VOLUME_HIGH
        return level

    def run(self):
        while True:
            volume = self._get_volume()
            if volume != self._volume:
                self._volume = volume
                self._set_index(volume)
                self.queue_draw()
            time.sleep(0.1)
