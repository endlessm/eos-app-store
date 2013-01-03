from icon_plugin import IconPlugin

from all_settings_view import AllSettingsView
from all_settings_presenter import AllSettingsPresenter
from all_settings_model import AllSettingsModel

class AllSettingsPlugin(IconPlugin):
    ICON_NAME = 'settings.png'
    def __init__(self, icon_size):
        self._all_settings_presenter = None
        super(AllSettingsPlugin, self).__init__(icon_size, [self.ICON_NAME], None, 0)
    
    def execute(self):
        if not self._all_settings_presenter:
            self._all_settings_presenter = AllSettingsPresenter(AllSettingsView(self), AllSettingsModel())
            self.connect('enter-notify-event', lambda w, e: self.disable_focus_out())
            self.connect('leave-notify-event', lambda w, e: self.enable_focus_out())
            
        self._all_settings_presenter.toggle_display()
        
    def enable_focus_out(self):
        self._all_settings_presenter.enable_focus_out()
        
    def disable_focus_out(self):
        self._all_settings_presenter.disable_focus_out()
        
            
