from icon_plugin import IconPlugin

class NetworkSettingsPlugin(IconPlugin):
    COMMAND = 'gnome-control-center --class=eos-network-manager network'
    ICON_NAME = 'network.png'
    
    def __init__(self, icon_size):
        super(NetworkSettingsPlugin, self).__init__(icon_size, self.ICON_NAME, self.COMMAND)
