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

    def test_default_chosen_repository_is_empty(self):
        self.assertEquals("", self._test_object.get_chosen_repository())

    def test_choosing_a_password_returns_repo_from_environment_manager(self):
        expected_repo = "expected repository"
        given_password = "expected password"

        def get_repo_from_password(password):
            if password == given_password:
                repo_def = Mock()
                repo_def.display_name = expected_repo
                return repo_def

        self._mock_env_manager.find_repo = Mock(side_effect=get_repo_from_password)

        self._test_object.choose_repository(given_password)
        self.assertEquals(expected_repo, self._test_object.get_chosen_repository())

    def test_changing_repositories_notifies_the_repository_changed_listener(self):
        listener = Mock()
        self._test_object.add_listener(RepoChooserModel.REPO_CHANGED, listener)

        self._test_object.choose_repository("something")

        self.assertTrue(listener.called)

    def test_do_update_calls_update_os_on_update_manager(self):
        self._test_object.do_update()

        self.assertTrue(self._mock_update_manager.update_os.called)

    def test_update_endpoint_url_when_user_changes_repository(self):
        expected_repo = "expected repository"
        given_password = "the password"

        def get_repo_from_password(password):
            if password == given_password:
                repo_def = Mock()
                repo_def.repo_url = expected_repo
                return repo_def
        self._mock_env_manager.find_repo = Mock(side_effect=get_repo_from_password)

        self._test_object.choose_repository(given_password)

        endpoint_provider.set_endless_url = Mock()

        self._test_object.do_update()
    
        endpoint_provider.set_endless_url.assert_called_with(expected_repo)

    def test_update_with_default_endpoint_url_when_user_changes_repository(self):
        default_url = endpoint_provider.get_endless_url()

        endpoint_provider.set_endless_url = Mock()

        self._test_object.do_update()
    
        endpoint_provider.set_endless_url.assert_called_with(default_url)


