import time

from threading import Thread
from wifi_util import WifiUtil
from icon_plugin import IconPlugin

class NetworkSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager network'
    ICON_NAMES = ['wifi_off.png', 'wifi_low.png', 'wifi_med.png', 'wifi_full.png'] 
    
    def __init__(self, icon_size):
        super(NetworkSettingsPlugin, self).__init__(icon_size, self.ICON_NAMES, self.COMMAND, 0)
        self._start_thread()
        
    def _set_icon(self, strength):
        print 'strength = ', strength
        if strength > 65:
            self._set_index(3)
        elif strength > 32:
            self._set_index(2)
        elif strength > 0:
            self._set_index(1)
        else:
            self._set_index(0)
        self.queue_draw()
        
    def _start_thread(self):
        update_thread = UpdateTasksThread(self._set_icon)
        update_thread.start()

class UpdateTasksThread(Thread):
    def __init__(self, callback):
        super(UpdateTasksThread, self).__init__()
        self.set_icon_callback = callback
    
    def run(self):
        while True :
            self.set_icon_callback(WifiUtil.get_strength())
            # Sleep so that we don't waste CPU cycles
            time.sleep(2)        
        
        
