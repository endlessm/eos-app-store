from icon_plugin import IconPlugin

class BluetoothSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-network-manager bluetooth'
    ICON_NAME = 'bluetooth.png'
    
    def __init__(self, icon_size):
        super(BluetoothSettingsPlugin, self).__init__(icon_size, self.ICON_NAME, self.COMMAND)
