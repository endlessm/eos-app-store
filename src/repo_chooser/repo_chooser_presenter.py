from repo_chooser_view import RepoChooserView
from repo_chooser_model import RepoChooserModel

class RepoChooserPresenter():
    def __init__(self, view, model):
        view.add_listener(RepoChooserView.SECRET_KEY_COMBO_PRESSED, view.prompt_for_password)
        view.add_listener(RepoChooserView.PASSWORD_ENTERED, lambda: self._handle_password_entered(view, model))
        view.add_listener(RepoChooserView.UPDATE_RESPONSE, lambda: self._handle_update_response(view, model))

        model.add_listener(RepoChooserModel.REPO_CHANGED, lambda: self._update_repo(view, model))

        self._update_repo(view, model)
        view.display()

    def _update_repo(self, view, model):
        view.set_repo_name(model.get_chosen_repository())

    def _handle_password_entered(self, view, model):
        if view.get_password_response():
            model.choose_repository(view.get_password())
        view.close_password_dialog()

    def _handle_update_response(self, view, model):
        if view.get_update_response():
            model.do_update()
        view.close_update_dialog()
