import unittest

from mock import Mock
from repo_chooser.repo_chooser_presenter import RepoChooserPresenter
from repo_chooser.repo_chooser_view import RepoChooserView
from repo_chooser.repo_chooser_model import RepoChooserModel

class RepoChooserPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()

        self._mock_view.add_listener = Mock(side_effect=self.view_add_listener)
        self._mock_model.add_listener = Mock(side_effect=self.model_add_listener)

    def model_add_listener(self, *args, **kwargs):
        if args[0] == RepoChooserModel.REPO_CHANGED:
            self._repo_changed_listener = args[1]
        
    def view_add_listener(self, *args, **kwargs):
        if args[0] == RepoChooserView.SECRET_KEY_COMBO_PRESSED:
            self._secret_key_combo_listener = args[1]
        elif args[0] == RepoChooserView.UPDATE_RESPONSE:
            self._update_response_listener = args[1]
        elif args[0] == RepoChooserView.PASSWORD_ENTERED:
            self._password_entered_listener = args[1]

    def test_updates_the_views_repo_name_from_the_model(self):
        chosen_repository = "default chosen repository"
        self._mock_model.get_chosen_repository = Mock(return_value=chosen_repository)

        RepoChooserPresenter(self._mock_view, self._mock_model)

        self._mock_view.set_repo_name.assert_called_once_with(chosen_repository)

    def test_whatever_is_returned_by_the_display_on_the_view_is_given_to_the_model(self):
        RepoChooserPresenter(self._mock_view, self._mock_model)

        self.assertTrue(self._mock_view.display.called)
        
    def test_when_secret_key_combo_is_pressed_then_launch_password_prompt(self):
        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._secret_key_combo_listener()

        self.assertTrue(self._mock_view.prompt_for_password.called)

    def test_when_user_enters_a_password_then_close_the_password_dialog(self):
        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._password_entered_listener()

        self.assertTrue(self._mock_view.close_password_dialog.called)

    def test_if_user_accepts_then_send_password_to_model(self):
        user_password = "some password"
        self._mock_view.get_password = Mock(return_value=user_password)
        self._mock_view.get_password_response = Mock(return_value=True)

        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._password_entered_listener()

        self._mock_model.choose_repository.assert_called_once_with(user_password)

    def test_if_user_rejects_then_dont_send_model_the_password(self):
        self._mock_view.get_password_response = Mock(return_value=False)

        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._password_entered_listener()

        self.assertFalse(self._mock_model.choose_repository.called)

    def test_update_response_listener_closes_update_dialog(self):
        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._update_response_listener()

        self.assertTrue(self._mock_view.close_update_dialog.called)

    def test_update_response_is_false_then_dont_update(self):
        self._mock_view.get_update_response = Mock(return_value=False)

        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._update_response_listener()

        self.assertFalse(self._mock_model.do_update.called)

    def test_update_response_is_true_then_do_update(self):
        self._mock_view.get_update_response = Mock(return_value=True)

        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._update_response_listener()

        self.assertTrue(self._mock_model.do_update.called)

    def test_repo_change_listener_updates_the_views_repo_name_from_the_model(self):
        chosen_repository = "chosen repository"
        self._mock_model.get_chosen_repository = Mock(return_value=chosen_repository)

        RepoChooserPresenter(self._mock_view, self._mock_model)
        self._mock_view.reset_mock()
        self._repo_changed_listener()

        self._mock_view.set_repo_name.assert_called_once_with(chosen_repository)
