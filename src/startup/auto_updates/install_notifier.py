from startup.auto_updates.install_notifier_view import InstallNotifierView
from startup.auto_updates.install_notifier_model import InstallNotifierModel
from startup.auto_updates.install_notifier_presenter import InstallNotifierPresenter

class InstallNotifier():
    USER_RESPONSE = "user.response"
    
    def __init__(self, model=InstallNotifierModel()):
        self._view = InstallNotifierView()
        self._model = model
    
    def notify_user(self):
        InstallNotifierPresenter(self._view, self._model)
        
    def should_install(self):
        return self._model.should_install()


if __name__ == "__main__":
    import gtk
    print InstallNotifier().notify_user()
    gtk.main()