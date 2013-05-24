import unittest
from mock import Mock, call
from desktop_files.folder_model import FolderModel
import tempfile
import shutil
import os
from xdg.DesktopEntry import DesktopEntry


class FolderModelTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_dir, True)
        except:
            pass

    def test_install_folder_in_directory(self):
        full_path = os.path.join(self._tmp_dir, 'Mydir')
        test_object = FolderModel('id', full_path, 'Name', 'Comment', 'Icon')
        
        test_object.install()
        
        self.assertTrue(os.path.isdir(full_path))
        
        self.assertTrue(os.path.isfile(os.path.join(full_path, ".directory")))
        de = DesktopEntry()
        de.parse(os.path.join(full_path, '.directory'))
        self.assertEquals('Name', de.getName())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
        
    def test_uninstall(self):
        full_path = os.path.join(self._tmp_dir, 'Mydir')
        test_object = FolderModel('id', full_path, 'Name', 'Comment', 'Icon')
        
        test_object.install()
        
        self.assertTrue(os.path.isdir(full_path))

        test_object.uninstall()
        
        self.assertFalse(os.path.isdir(full_path))

    def test_simulate_installing_copied_desktop_file_from_app_store(self):
        full_path = os.path.join(self._tmp_dir, 'Mydir')
        test_object = FolderModel('id', full_path, 'Name', 'Comment', 'Icon')

        new_path = os.path.join(self._tmp_dir, 'NewDir')
        test_object.set_file_path(new_path)
        test_object.install()

        self.assertTrue(os.path.isdir(new_path))
        self.assertTrue(os.path.isfile(os.path.join(new_path, ".directory")))
        de = DesktopEntry()
        de.parse(os.path.join(new_path, '.directory'))
        self.assertEquals('Name', de.getName())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
