import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
import tempfile
import shutil
import os
from application_store.application_store_model import ApplicationStoreModel
from sets import ImmutableSet
from application_store.application_store_errors import ApplicationStoreError
from application_store.category_model import CategoryModel
from mock import Mock


class ApplicationStoreIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self._view = FakeView()
        self._app_store_dir = tempfile.mkdtemp()
        self.desktop_presenter = Mock()
        self.desktop_presenter.refresh_view = Mock()
        self._presenter = ApplicationStorePresenter(self.desktop_presenter, self._view, ApplicationStoreModel(self._app_store_dir))
        

    def _remove_temporary_directory(self):
        return shutil.rmtree(self._app_store_dir)

    def tearDown(self):
        self._remove_temporary_directory()
        
    def test_categories_throws_an_exception_if_the_app_store_directory_does_not_exist(self):
        self._presenter = ApplicationStorePresenter(self.desktop_presenter, self._view, ApplicationStoreModel('non/existant/directory'))
        
        self.assertRaises(ApplicationStoreError, self._presenter.show_categories)

    def test_categories_sends_an_empty_list_to_the_view_if_there_are_no_desktop_files(self):
        self._presenter.show_categories()
        
        self.assertEquals(ImmutableSet([]), self._view.categories)

    def test_categories_sends_single_list_to_the_view_if_there_is_any_desktop_files(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Video\nType=Application\nName=app1\nExec=foo')        
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Games;Audio\nType=Application\nName=app2\nExec=bar')
        expected_categories = ImmutableSet([CategoryModel('Audio'), CategoryModel('Games'), CategoryModel('Video')])
        
        self._presenter.show_categories()
        
        self.assertEquals(expected_categories, self._view.categories)
    
    def test_show_category_displays_all_the_applications_in_that_category(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')        
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app2\nExec=bar')
        self._presenter.show_categories()
        
        self._view.click_category(0)
        
        self.assertEquals(self._view._category_list[0].get_applications_set(), self._view.applications_set)
    
    def test_installing_an_application(self):
        self._make_file(self._app_store_dir, 'app1.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app1\nExec=foo')        
        self._make_file(self._app_store_dir, 'app2.desktop', '[Desktop Entry]\nCategories=Audio\nType=Application\nName=app2\nExec=bar')
        self._presenter.show_categories()
        self._view.click_category(0)
        
        installed_application = self._view._application_list[0]
        
        self._view.install_application(0)        
        
        self.assertNotIn(installed_application, self._view.applications_set)

    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()


class FakeView():
    def set_presenter(self, presenter):
        self._presenter = presenter
        
    def click_category(self, category_index):
        self._presenter.show_category(self._category_list[category_index])
        
    def show_categories(self, categories):
        self.categories = categories
        self._category_list = []
        for cat in categories:
            self._category_list.append(cat)
    
    def show_category(self, applications_set):
        self.applications_set = applications_set
        self._application_list = []
        for app in applications_set:
            self._application_list.append(app)
    
    def install_application(self, application_index):
        self._presenter.install_application(self._application_list[application_index])
        