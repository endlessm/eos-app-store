from startup.auto_updates.install_notifier_view import InstallNotifierView

class InstallNotifierPresenter():
    def __init__(self, view, model):
        view.add_listener(InstallNotifierView.RESTART_NOW, lambda: self._install_later(view, model))
        view.add_listener(InstallNotifierView.RESTART_LATER, lambda: self._install_now(view, model))
        
        view.set_new_version(model.get_new_version())
        view.display()

    def _install_later(self, view, model):
        view.close()
        model.install_now()

    def _install_now(self, view, model):
        view.close()
        model.install_later()