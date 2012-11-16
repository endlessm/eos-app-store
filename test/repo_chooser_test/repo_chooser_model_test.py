import unittest
from mock import Mock

from repo_chooser.repo_chooser_model import RepoChooserModel
from startup.auto_updates import endpoint_provider

class RepoChooserModelTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_env_manager = Mock()
        self._mock_update_manager = Mock()

        self._test_object = RepoChooserModel(self._mock_env_manager, self._mock_update_manager)
        
        self._original_endpoint_provider = endpoint_provider.set_endless_url

    def tearDown(self):
        endpoint_provider.set_endless_url = self._original_endpoint_provider

    def test_default_chosen_repository_is_whatever_environment_manager_gives_us(self):
        expected_repo = "expected repo"
        self._mock_env_manager.get_current_repo = Mock(return_value=expected_repo)

        self.assertEquals(expected_repo, self._test_object.get_chosen_repository())

    def test_choosing_a_password_returns_repo_from_environment_manager(self):
        given_password = "this is the given password"

        self._test_object.choose_repository(given_password)

        self._mock_env_manager.set_current_repo.assert_called_once_with(given_password)

    def test_changing_repositories_notifies_the_repository_changed_listener(self):
        listener = Mock()
        self._test_object.add_listener(RepoChooserModel.REPO_CHANGED, listener)

        self._test_object.choose_repository("something")

        self.assertTrue(listener.called)

    def test_do_update_calls_update_os_on_update_manager(self):
        self._test_object.do_update()

        self.assertTrue(self._mock_update_manager.update_os.called)

