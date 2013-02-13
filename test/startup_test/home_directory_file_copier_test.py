import unittest
from startup.home_directory_file_copier import HomeDirectoryFileCopier
import os

from mock import Mock

class HomeDirectoryFileCopierTest(unittest.TestCase):
    def setUp(self):
        self._path_prefix = "this is the path prefix"

        self._mock_manager = Mock()
        self._mock_home_path_provider = self._mock_manager.home_path_provider
        self._mock_copier = self._mock_manager.copier

        self._test_object = HomeDirectoryFileCopier(self._mock_home_path_provider, self._mock_copier)

    def test_destination_folder_is_passed_to_homepath_provider(self):
        destination = "this is the destination"

        self._test_object.copy("this is the source", destination)

        self._mock_home_path_provider.get_user_directory.assert_called_once_with(destination)

    def test_homepath_provider_is_used_to_call_copy_tree(self):
        source = "this is the source"
        destination = "this is the destination"
        home_path = "this is the home path"

        self._mock_home_path_provider.get_user_directory = Mock(return_value=home_path)

        self._test_object.copy(source, destination)

        self._mock_copier.assert_called_once_with(source, home_path)
