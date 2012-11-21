import unittest
from desktop.desktop_model import DesktopModel
import tempfile
import shutil
import os
from application_store.desktop_file_utilities import DesktopFileUtilities

class TestDesktopModel(unittest.TestCase):
    
    def setUp(self):
        self._tmp_directory = tempfile.mkdtemp()
        self._test_object = DesktopModel()
        self._file_helper = DesktopFileUtilities()
               
    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_directory, True)
        except:
            pass
        
    def test_empty_desktop_directory_returns_empty_list(self):
        self.assertEquals([], self._test_object.get_shortcuts(self._tmp_directory))
        

    def test_files_in_directory_are_returned(self):
        self._build_desktop()
        shortcuts = self._test_object.get_shortcuts(self._tmp_directory)
        self.assertEquals(set(['link1.desktop', 'link2.desktop', 'link3.desktop']), set(shortcuts))
        self.assertTrue(os.path.isfile(os.path.join(self._tmp_directory, '.order')))

#    def test_order_file_gets_created_when_not_already_existing(self):
#        self.assertEquals([], self._test_object.get_shortcuts(self._tmp_directory))
#        self.assertTrue(os.path.isfile(os.path.join(self._tmp_directory, '.order')))

    def _build_desktop(self):
        self._make_file(self._tmp_directory, 'link1.desktop', 
                        '[Desktop Entry]\nCategories=Network\nType=Link\nName=link1\nURL=foo1\nComment=comment1\nX-EndlessM-Normal-Icon=iNorm\nX-EndlessM-Hover-Icon=iHover\nX-EndlessM-Down-Icon=iDown')        
        self._make_file(self._tmp_directory, 'link2.desktop', 
                        '[Desktop Entry]\nCategories=Network\nType=Link\nName=link2\nURL=foo2\nComment=comment2')        
        self._make_file(self._tmp_directory, 'link3.desktop', 
                        '[Desktop Entry]\nCategories=Network\nType=Application\nName=link3\nComment=comment3\nURL=foo3\nExec=firefox\nX-EndlessM-Normal-Icon=iNorm\nX-EndlessM-Hover-Icon=iHover\nX-EndlessM-Down-Icon=iDown')        

    def _make_file(self, dirname, filename, content):
        with open(os.path.join(dirname, filename), 'w') as f: 
            f.write(content)
