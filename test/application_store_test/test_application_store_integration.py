import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
import tempfile
import shutil
import os
from application_store.application_store_model import ApplicationStoreModel,\
    Category
from sets import ImmutableSet
from application_store.application_store_errors import ApplicationStoreError


class ApplicationStoreIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self._view = FakeView()
        self._app_store_dir = tempfile.mkdtemp()
        self._test_object = ApplicationStorePresenter(self._view, ApplicationStoreModel(self._app_store_dir))
        

    def _remove_temporary_directory(self):
        return shutil.rmtree(self._app_store_dir)

    def tearDown(self):
        self._remove_temporary_directory()
        
    def test_categories_throws_an_exception_if_the_app_store_directory_does_not_exist(self):
        self._test_object = ApplicationStorePresenter(self._view, ApplicationStoreModel('non/existant/directory'))
        self.assertRaises(ApplicationStoreError, self._test_object.show_categories)

    def test_categories_sends_an_empty_list_to_the_view_if_there_are_no_desktop_files(self):
        self._test_object.show_categories()
        self.assertEquals(ImmutableSet([]), self._view.categories)

    def test_categories_sends_single_list_to_the_view_if_there_is_any_desktop_files(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Video\nType=Application\nName=app1\nExec=foo')        
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Games;Audio\nType=Application\nName=app2\nExec=bar')
        expected_categories = ImmutableSet([Category('Audio'), Category('Games'), Category('Video')])
        
        self._test_object.show_categories()
        
        self.assertEquals(expected_categories, self._view.categories)

    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()


class FakeView():
    def show_categories(self, categories):
        self.categories = categories