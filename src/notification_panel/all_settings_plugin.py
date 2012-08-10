from icon_plugin import IconPlugin

class AllSettingsPlugin(IconPlugin):
    COMMAND = 'gnome-control-center --class=eos-network-manager'
    ICON_NAME = 'settings.png'
    
    def __init__(self, icon_size):
        super(AllSettingsPlugin, self).__init__(icon_size, self.ICON_NAME, self.COMMAND)
        