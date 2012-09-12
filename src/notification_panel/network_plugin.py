import dbus

from icon_plugin import IconPlugin
from dbus.mainloop.glib import DBusGMainLoop 

class NetworkSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager network'
    ICON_NAME = 'network.png'
    
    def __init__(self, icon_size):
        super(NetworkSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], self.COMMAND)
        self.bus = dbus.SystemBus()
        NetworkManager
        self.bus.get_object('org.freedesktop/NetworkManager/Devices/eth0')
        self.bus.add_signal_receiver(self.handle_change, None, self.NM + '.AccessPoint', None, None)