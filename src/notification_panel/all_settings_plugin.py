import gtk
import os

from icon_plugin import IconPlugin

from all_settings_view import AllSettingsView
from all_settings_presenter import AllSettingsPresenter
from all_settings_model import AllSettingsModel

class AllSettingsPlugin(IconPlugin):
    ICON_NAME = 'settings.png'
    def __init__(self, icon_size, desktop_preferences):
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0)
        self._desktop_preferences = desktop_preferences
        
    def execute(self):
        AllSettingsPresenter(AllSettingsView(self, self._desktop_preferences), AllSettingsModel())

