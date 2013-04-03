import unittest
from mock import Mock, call
from desktop_files.application_model import ApplicationModel
import tempfile
import shutil
import os
from xdg.DesktopEntry import DesktopEntry


class ApplicationModelTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_dir, True)
        except:
            pass

    def test_a_model_with_the_same_application_id_is_equal(self):
        id = Mock()
        self.assertEquals(ApplicationModel(id, Mock(), None), ApplicationModel(id, Mock(), ["Video"]))
    
    def test_a_model_with_a_different_id_is_not_equal(self):
        self.assertNotEqual(ApplicationModel(Mock(), Mock(), None), ApplicationModel(Mock(), Mock(), None))
    
    def test_the_hash_is_based_on_the_id(self):
        id = Mock()
        self.assertEquals(id.__hash__(), ApplicationModel(id, Mock(), None).__hash__())
    
    def test_categories(self):
        self.assertEquals(['All'], ApplicationModel(Mock(), Mock(), []).get_categories())
        
    def test_visit_categories(self):
        test_object = ApplicationModel('id', Mock(), ["Audio", "Video"])
        visitor = Mock()
        
        test_object.visit_categories(visitor)
        
        visitor.assert_was_called_once_with("All", test_object)
        
    def test_install_application_in_directory(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = ApplicationModel('id', full_path, ["Audio", "Video"], 'Name', 'Comment', 'Icon', 'ClassName')
        
        test_object.install()
        
        self.assertTrue(os.path.isfile(full_path))
        de = DesktopEntry()
        de.parse(full_path)
        self.assertEquals('Name', de.getName())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
        self.assertEquals('ClassName', de.get('X-EndlessM-Class-Name'))
        
    def test_uninstall(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = ApplicationModel('id', full_path, ["Audio", "Video"], 'Name', 'Comment', 'Icon', 'ClassName')
        
        test_object.install()
        
        self.assertTrue(os.path.isfile(full_path))

        test_object.uninstall()
        
        self.assertFalse(os.path.isfile(full_path))
        
    def test_simulate_installing_copied_desktop_file_from_app_store(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = ApplicationModel('id', full_path, ["Audio", "Video"], 'Name', 'Comment', 'Icon', 'ClassName')

        new_path = os.path.join(self._tmp_dir, 'different-file.desktop')
        test_object.set_file_path(new_path)
        test_object.install()

        self.assertTrue(os.path.isfile(new_path))
        de = DesktopEntry()
        de.parse(new_path)
        self.assertEquals('Name', de.getName())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
        self.assertEquals('ClassName', de.get('X-EndlessM-Class-Name'))
