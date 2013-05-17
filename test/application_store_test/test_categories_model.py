import unittest
from mock import Mock
from application_store.categories_model import CategoriesModel
from application_store.category_model import CategoryModel


class CategoriesModelTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = CategoriesModel()

    def test_adding_an_application(self):
        application = Mock()
        self._test_object.add('category_name', application)
        
        self.assertEquals(frozenset([CategoryModel('category_name')]), self._test_object.get_categories_set())

    def test_adding_application_twice(self):
        application = Mock()
        self._test_object.add('category_name', application)
        self._test_object.add('category_name', application)
        
        self.assertEquals(frozenset([CategoryModel('category_name')]), self._test_object.get_categories_set())

    def test_adding_two_different_applications_in_same_category(self):
        self._test_object.add('category_name', Mock())
        self._test_object.add('category_name', Mock())
        
        self.assertEquals(frozenset([CategoryModel('category_name')]), self._test_object.get_categories_set())

    def test_adding_two_different_applications_in_different_categories(self):
        self._test_object.add('category_1', Mock())
        self._test_object.add('category_2', Mock())
        
        self.assertEquals(frozenset([CategoryModel('category_1'), CategoryModel('category_2')]), self._test_object.get_categories_set())

    def test_visiting_added_application(self):
        application = Mock()
        application.visit_categories = Mock()
        
        self._test_object.add_application(application)
        
        application.visit_categories.assert_called_once_with(self._test_object.add)

    def test_refreshing_stale_category(self):
        app1 = Mock()
        self._test_object.add('category_1', app1)
        self._test_object.add('category_2', Mock())
        stale_category = CategoryModel('category_1')

        refreshed_category = self._test_object.get_updated_category(stale_category)
        
        self.assertIsNot(stale_category, refreshed_category)
        self.assertIn(app1, refreshed_category.get_applications_set())
