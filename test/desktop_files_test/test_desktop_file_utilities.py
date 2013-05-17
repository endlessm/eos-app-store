import os
from mock import Mock

import shutil
from desktop_files.desktop_file_utilities import DesktopFileUtilities
from desktop_files.application_model import ApplicationModel
from desktop_files.link_model import LinkModel
from desktop_files.folder_model import FolderModel
import tempfile
import unittest

class DesktopFileUtilitiesTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

        self._make_file(self._tmp_dir, 'link1.desktop',
                        '[Desktop Entry]\nCategories=Network\nType=Link\nName=link1\nURL=foo1\nComment=comment1\nIcon=icon1\nX-EndlessM-Class-Name=class_name1')
        self._make_file(self._tmp_dir, 'link2.desktop',
                        '[Desktop Entry]\nCategories=Network\nType=Link\nName=link2\nURL=foo2\nComment=comment2')
        self._make_file(self._tmp_dir, 'link3.desktop',
                        '[Desktop Entry]\nCategories=Network\nType=Application\nName=link3\nComment=comment3\nURL=foo3\nExec=firefox\nIcon=icon3')

        self.junk_dir = os.path.join(self._tmp_dir, "junk")
        os.makedirs(self.junk_dir)

        self._test_object = DesktopFileUtilities()
               
    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_dir, True)
        except:
            pass
        
    def test_get_apps_returns_contents_of_dekstop_files(self):
        files = self._test_object.get_desktop_files_and_folders(self._tmp_dir)
        self.assertEquals(set(files), set(['link1.desktop', 'link2.desktop', 'link3.desktop', 'junk']))

    def test_get_contents_of_dekstop_files_and_folders(self):
        files = self._test_object.get_desktop_files(self._tmp_dir)
        self.assertEquals(set(files), set(['link1.desktop', 'link2.desktop', 'link3.desktop']))

    def test_application_model_creation_from_file(self):
        model = self._test_object.create_model(os.path.join(self._tmp_dir, 'link3.desktop'), 'link3.desktop')
        self.assertIsInstance(model, ApplicationModel)
        self.assertEquals('link3.desktop', model.id())
        self.assertEquals('link3', model.name())
        self.assertEquals('comment3', model.comment())
        self.assertEquals('icon3', model.icon())
        self.assertEquals('firefox', model.class_name())

    def test_link_model_creation_from_file(self):
        model = self._test_object.create_model(os.path.join(self._tmp_dir, 'link1.desktop'), 'link1.desktop')
        self.assertIsInstance(model, LinkModel)
        self.assertEquals('link1', model.name())
        self.assertEquals('foo1', model.url())
        self.assertEquals('comment1', model.comment())
        self.assertEquals('icon1', model.icon())
        self.assertEquals('/usr/share/endlessm/icons/apps/icon1_normal.png', model.normal_icon())
        self.assertEquals('/usr/share/endlessm/icons/apps/icon1_down.png', model.down_icon())
        self.assertEquals('/usr/share/endlessm/icons/apps/icon1_hover.png', model.hover_icon())
        self.assertEquals('/usr/share/endlessm/icons/mini/icon1_normal.png', model.mini_icon())
        self.assertEquals('class_name1', model.class_name())

    def test_link_model_creation_from_incomplete_file(self):
        model = self._test_object.create_model(os.path.join(self._tmp_dir, 'link2.desktop'), 'link2.desktop')
        self.assertIsInstance(model, LinkModel)
        self.assertEquals('link2', model.name())
        self.assertEquals('foo2', model.url())
        self.assertEquals('comment2', model.comment())
        self.assertEquals('', model.icon())
        self.assertEquals('', model.normal_icon())
        self.assertEquals('', model.down_icon())
        self.assertEquals('', model.hover_icon())
        self.assertEquals('', model.mini_icon())
        self.assertEquals('', model.class_name())
        
    def test_folder_model_creation_from_file(self):
        self._make_file(self.junk_dir, '.directory',
                        '[Desktop Entry]\nType=Directory\nName=Junk Dir\nComment=comment4\nIcon=icon4')
        model = self._test_object.create_model(self.junk_dir, 'junk')
        self.assertIsInstance(model, FolderModel)
        self.assertEquals('junk', model.id())
        self.assertEquals('Junk Dir', model.name())
        self.assertEquals('comment4', model.comment())
        self.assertEquals('icon4', model.icon())
        self.assertEquals('/usr/share/endlessm/icons/folders/icon4_normal.png', model.normal_icon())
        self.assertEquals('/usr/share/endlessm/icons/folders/icon4_down.png', model.down_icon())
        self.assertEquals('/usr/share/endlessm/icons/folders/icon4_hover.png', model.hover_icon())

    def test_folder_model_creation_from_folder_without_file(self):
        model = self._test_object.create_model(self.junk_dir, 'junk')
        self.assertIsInstance(model, FolderModel)
        self.assertEquals('junk', model.id())
        self.assertEquals('junk', model.name())
        self.assertEquals('', model.comment())
        self.assertEquals('', model.icon())
        self.assertEquals('', model.normal_icon())
        self.assertEquals('', model.down_icon())
        self.assertEquals('', model.hover_icon())

    def test_return_all_desktop_models_in_a_directory(self):
        desktop_model_1 = Mock()
        desktop_model_2 = Mock()
        desktop_model_3 = Mock()
        desktop_model_4 = Mock()
        invalid_desktop_model = Mock()
        def mock_create_model(file_path, file_name):
            if file_path == os.path.join(self._tmp_dir, 'link1.desktop') and file_name == 'link1.desktop':
                return desktop_model_1
            elif file_path == os.path.join(self._tmp_dir, 'link2.desktop') and file_name == 'link2.desktop':
                return desktop_model_2
            elif file_path == os.path.join(self._tmp_dir, 'link3.desktop') and file_name == 'link3.desktop':
                return desktop_model_3
            elif file_path == os.path.join(self._tmp_dir, 'junk') and file_name == 'junk':
                return desktop_model_4
            else:
                return invalid_desktop_model
        self._test_object.create_model = mock_create_model
        
        desktop_file_models = self._test_object.get_desktop_file_models(self._tmp_dir)
        
        self.assertEquals(set(desktop_file_models), set([desktop_model_1, desktop_model_2, desktop_model_3, desktop_model_4]))
        
    def _make_file(self, dirname, filename, content):
        with open(os.path.join(dirname, filename), 'w') as f: 
            f.write(content)
