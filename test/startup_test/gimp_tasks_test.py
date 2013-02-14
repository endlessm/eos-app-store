import unittest
from mock import Mock, call

from startup.gimp_tasks import GimpTasks

class GimpTasksTest(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.directory_creator = self.mock_manager.directory_creator
        self.copy = self.mock_manager.copy
        self.home_path_provider = Mock()
        self._test_object = GimpTasks(self.copy, self.directory_creator, self.home_path_provider)

    def test_copies_sessionrc_to_users_home(self):
        destination_file = "destination file"
        destination_directory = "destination dir"

        def get_user_dir_side_effect(*args, **kwargs):
            if args[0] == self._test_object.TARGET:
                return destination_file
            elif args[0] == self._test_object.TARGET_DIR:
                return destination_directory
        self.home_path_provider.get_user_directory = Mock(side_effect=get_user_dir_side_effect)

        self._test_object.execute()

        expected_calls = [
            call.directory_creator(destination_directory),
            call.copy(self._test_object.SOURCE, destination_file)
            ]
        self.assertEquals(self.mock_manager.mock_calls, expected_calls)

