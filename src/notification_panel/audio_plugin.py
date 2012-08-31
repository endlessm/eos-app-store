import threading
import alsaaudio
import time

from icon_plugin import IconPlugin

class AudioSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-audio-manager sound'
    ICON_NAMES = ['audio-volume-muted.png',
                  'audio-volume-low.png',
                  'audio-volume-medium.png',
                  'audio-volume-high.png']

    VOLUME_MUTED = 0
    VOLUME_LOW = 1
    VOLUME_MED = 2
    VOLUME_HIGH = 3
    
    def __init__(self, icon_size):
        super(AudioSettingsPlugin, self).__init__(icon_size, self.ICON_NAMES, self.COMMAND, self.VOLUME_MED)
        self._volume_thread = UpdateVolumeThread()
        self._volume_thread.start()

class UpdateVolumeThread(threading.Thread):
    def run(self):
        while True:
            master = alsaaudio.mixer()
            print master.getvolume()
            time.sleep(1)
        
