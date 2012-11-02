from startup.auto_updates.install_notifier_view import InstallNotifierView
from startup.auto_updates.install_notifier_model import InstallNotifierModel
from startup.auto_updates.install_notifier_presenter import InstallNotifierPresenter
from ui.abstract_notifier import AbstractNotifier

class InstallNotifier(AbstractNotifier):
    USER_RESPONSE = "user.response"
    
    def __init__(self, model=InstallNotifierModel()):
        self._model = model
        self._model.add_listener(InstallNotifierModel.ACTION_TAKEN, lambda: self._notify(self.USER_RESPONSE))
    
    def notify_user(self):
        InstallNotifierPresenter(InstallNotifierView(), self._model)
        
    def should_install(self):
        return self._model.should_install()



if __name__ == "__main__":
    import gtk
    notifier = InstallNotifier()
    def stupid_head(notifier):
        print notifier.should_install()
    notifier.add_listener(InstallNotifier.USER_RESPONSE, lambda: stupid_head(notifier))
    notifier.notify_user()
    gtk.main()
    
