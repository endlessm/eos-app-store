from osapps.app_launcher import AppLauncher

class AllSettingsPresenter(object):
    def __init__(self, app_launcher=AppLauncher()):
        self._app_launcher = app_launcher

    def launch(self):
        self._app_launcher.launch(self.get_path())
        
    def get_path(self):
        return "/usr/bin/eos-settings"
