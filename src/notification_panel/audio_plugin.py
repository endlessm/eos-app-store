from icon_plugin import IconPlugin

class AudioSettingsPlugin(IconPlugin):
    COMMAND = 'sudo gnome-control-center --class=eos-audio-manager sound'
    ICON_NAME = 'audio-volume-medium.png'
    
    def __init__(self, icon_size):
        super(AudioSettingsPlugin, self).__init__(icon_size, self.ICON_NAME, self.COMMAND)
