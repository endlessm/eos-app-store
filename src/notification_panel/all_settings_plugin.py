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
        _all_settings_view = AllSettingsView(self)
 
        print "Am I open in the plugin:",  _all_settings_view.is_displayed()
        
        if not self._all_settings_presenter:
            self._all_settings_presenter = AllSettingsPresenter(_all_settings_view, AllSettingsModel())
            
        self._all_settings_presenter.show_dropdown()
            
