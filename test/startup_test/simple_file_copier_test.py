import unittest
from startup.simple_file_copier import SimpleFileCopier

from mock import Mock

class DefaultFileCopierTest(unittest.TestCase):
    def setUp(self):
        self.test_source = "source"
        self.destination_folder = "dest_folder"
        self.destination_path = "dest_path"
        
        self.home_path_provider = Mock()
        self.home_path_provider.get_user_directory = Mock(return_value = self.destination_path)
        
        self.copier = Mock()
        self.test_object = SimpleFileCopier(self.destination_folder, self.home_path_provider,
                self.copier)        
    
    def test_homepath_provider_is_used_to_call_copy_tree(self):
        self.test_object.copy_from(self.test_source)
        
        self.home_path_provider.get_user_directory.assert_called_once_with(self.destination_folder)
        self.copier.assert_called_once_with(self.test_source, self.destination_path)
