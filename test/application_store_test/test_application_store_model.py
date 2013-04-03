import os
from mock import Mock
from application_store.application_store_model import ApplicationStoreModel
from application_store.application_store_errors import ApplicationStoreWrappedException
from application_store.category_model import CategoryModel
import unittest
import shutil
import tempfile


class ApplicationStoreModelTestCase(unittest.TestCase):

    def setUp(self):
        self._app_store_dir = tempfile.mkdtemp()
        self._application_list_model = Mock()
        self._application_list_model.is_installed = Mock(return_value=False)
        self._test_object = ApplicationStoreModel(self._app_store_dir, self._app_store_dir, self._application_list_model)

    def tearDown(self):
        try:
            shutil.rmtree(self._app_store_dir, True)
        except:
            pass

    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()

    def test_when_there_is_no_directory_categories_wraps_the_exception(self):
        self.assertRaises(ApplicationStoreWrappedException, ApplicationStoreModel('NonExistantDir', 'NonExistantDir').get_categories)

    def test_get_categories_returns_an_empty_list_when_there_are_no_files(self):
        self.assertEquals(frozenset([]), self._test_object.get_categories())

    def test_get_categories_returns_an_empty_list_when_there_are_no_categories(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nType=Application\nName=app1\nExec=foo')
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nType=Application\nName=app2\nExec=bar')
        self.assertEquals(frozenset([CategoryModel('All')]), self._test_object.get_categories())

    def test_get_categories_returns_single_category_from_single_file(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')
        self.assertEquals(frozenset([CategoryModel('All')]), self._test_object.get_categories())

    def test_two_files_with_same_category(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app2\nExec=bar')
        self.assertEquals(frozenset([CategoryModel('All')]), self._test_object.get_categories())

    def test_two_files_with_different_categories(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Games\nType=Application\nName=app2\nExec=bar')
        self.assertEquals(frozenset([CategoryModel('All'), CategoryModel('All')]), self._test_object.get_categories())

    def test_file_with_multiple_categories(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio;Games\nType=Application\nName=app1\nExec=foo')
        self.assertEquals(frozenset([CategoryModel('All'), CategoryModel('All')]), self._test_object.get_categories())

    def test_an_installed_application_does_not_show_in_categories(self):
        self._test_object = ApplicationStoreModel(self._app_store_dir, self._app_store_dir, FakeInstalledAppModel())
        self._make_file(self._app_store_dir, 'installed.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Games\nType=Application\nName=app2\nExec=bar')
        self.assertEquals(frozenset([CategoryModel('All')]), self._test_object.get_categories())

    def test_install_application(self):
        application = Mock()
        application_id = Mock()
        application.id = Mock(return_value = application_id)

        self._test_object.install(application)

        self._application_list_model.install.assert_called_once_with(application_id)

class FakeInstalledAppModel():
    def set_data_dir(self, dir):
        pass

    def is_installed(self, application):
        return application == 'installed.desktop'
