import unittest
from add_shortcuts_module.add_shortcuts_model import AddShortcutsModel
from mock import Mock

class TestAddShortcutsModel(unittest.TestCase):
    def setUp(self):
        self.available_icons_bad = ['folder1.svg', 'folder2.png', 'folder3.icon', 'blah.png']
        self.available_icons_good = ['folder1.svg', 'folder2.png']
        self.path = '/tmp/'
        self.default_path = '~/'
        self.directory_name = 'my folder'
        
        self.test_object = AddShortcutsModel()
        self.test_object.get_icon_list = Mock(return_value=self.available_icons_bad)
        
    
    def test_get_category_data(self):
        # method returns harcoded values, no functionality to test
        # if way of obtaining category data is changed, test must be written
        pass
    
    def test_create_directory(self):
        self.assertEqual(self.default_path+self.directory_name, self.test_object.create_directory(self.directory_name))
        self.assertEqual(self.path+self.directory_name, self.test_object.create_directory(self.directory_name, self.path))
    
    def test_folder_icons(self):
        self.assertEqual(self.available_icons_good, self.test_object.get_folder_icons('', 'folder'))