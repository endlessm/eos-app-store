import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
from mock import Mock
import tempfile
import shutil
import os
from application_store.application_store_model import ApplicationStoreModel
from sets import ImmutableSet


class ApplicationStoreIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self._view = Mock()
        self._app_store_dir = tempfile.mkdtemp()
        self._test_object = ApplicationStorePresenter(self._view, ApplicationStoreModel(self._app_store_dir))
        

    def _remove_temporary_directory(self):
        return shutil.rmtree(self._app_store_dir)

    def tearDown(self):
        self._remove_temporary_directory()

    def test_categories_sends_an_empty_list_to_the_view_if_there_are_no_desktop_files(self):
        self._view.show_categories = Mock()
        
        self._test_object.show_categories()
        
        self._view.show_categories.assert_called_once_with(ImmutableSet([]))

    def test_categories_sends_single_list_to_the_view_if_there_is_any_desktop_files(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Video\nType=Application\nName=app1\nExec=foo')        
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Games;Audio\nType=Application\nName=app2\nExec=bar')
        
        self._view.show_categories = Mock()
        
        self._test_object.show_categories()
        
        self._view.show_categories.assert_called_once_with(ImmutableSet(['Audio', 'Games', 'Video']))

    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()
