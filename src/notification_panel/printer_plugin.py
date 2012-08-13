from icon_plugin import IconPlugin

class PrinterSettingsPlugin(IconPlugin):
    COMMAND = 'system-config-printer --class=eos-printers'
    ICON_NAME = 'printer.png'
    
    def __init__(self, icon_size):
        super(PrinterSettingsPlugin, self).__init__(icon_size, self.ICON_NAME, self.COMMAND)
