import gtk
import os

from icon_plugin import IconPlugin

from all_settings_view import AllSettingsView
from all_settings_presenter import AllSettingsPresenter
from all_settings_model import AllSettingsModel

class AllSettingsPlugin(IconPlugin):
    ICON_NAME = 'settings.png'
    def __init__(self, icon_size):
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0)
        
    def execute(self):
        AllSettingsPresenter(AllSettingsView(self), AllSettingsModel())

