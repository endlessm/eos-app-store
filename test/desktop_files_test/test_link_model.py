import unittest
from mock import Mock, call
from desktop_files.link_model import LinkModel
import tempfile
import shutil
import os
from xdg.DesktopEntry import DesktopEntry


class LinkModelTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_dir, True)
        except:
            pass

    def test_install_link_in_directory(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = LinkModel(full_path, 'Name', 'Url', 'Comment', 'Icon', 'ClassName')
        
        test_object.install()
        
        self.assertTrue(os.path.isfile(full_path))
        de = DesktopEntry()
        de.parse(full_path)
        self.assertEquals('Name', de.getName())
        self.assertEquals('Url', de.getURL())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
        self.assertEquals('ClassName', de.get('X-EndlessM-Class-Name'))
        
    def test_uninstall(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = LinkModel(full_path, 'Name', 'Url', 'Comment', 'Icon', 'ClassName')
        
        test_object.install()
        
        self.assertTrue(os.path.isfile(full_path))

        test_object.uninstall()
        
        self.assertFalse(os.path.isfile(full_path))
        
    def test_simulate_installing_copied_desktop_file_from_app_store(self):
        full_path = os.path.join(self._tmp_dir, 'something.desktop')
        test_object = LinkModel(full_path, 'Name', 'Url', 'Comment', 'Icon', 'ClassName')

        new_path = os.path.join(self._tmp_dir, 'different-file.desktop')
        test_object.set_file_path(new_path)
        test_object.install()

        self.assertTrue(os.path.isfile(new_path))
        de = DesktopEntry()
        de.parse(new_path)
        self.assertEquals('Name', de.getName())
        self.assertEquals('Url', de.getURL())
        self.assertEquals('Comment', de.getComment())
        self.assertEquals('Icon', de.getIcon())
        self.assertEquals('ClassName', de.get('X-EndlessM-Class-Name'))
