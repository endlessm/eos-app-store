import unittest
from mock import Mock

from startup.gimp_tasks import GimpTasks

class GimpTasksTest(unittest.TestCase):
    def setUp(self):
        mock_manager = Mock()
        self.copier = mock_manager.copier
        self.home_path_provider = mock_manager.home_path_provider
        self._test_object = GimpTasks(self.copier, self.home_path_provider)

    def test_copies_sessionrc_to_users_home(self):
        destination = "destination"
        self.home_path_provider.get_user_directory = Mock(return_value=destination)

        self._test_object.execute()

        self.copier.assert_called_once_with(self._test_object.SOURCE, destination)

    def test_get_user_directory_called_with_target_filename(self):
        self._test_object.execute()

        self.home_path_provider.get_user_directory.assert_called_once_with(self._test_object.TARGET)

