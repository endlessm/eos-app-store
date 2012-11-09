import unittest
from mock import Mock
from application_store.category_model import CategoryModel
from sets import ImmutableSet


class CategoryModelTestCase(unittest.TestCase):
    def test_a_model_with_the_same_name_is_equal(self):
        name = Mock()
        self.assertEquals(CategoryModel(name), CategoryModel(name))
    
    def test_a_model_with_a_different_name_is_not_equal(self):
        self.assertNotEqual(CategoryModel(Mock()), CategoryModel(Mock()))
    
    def test_the_hash_is_based_on_the_name(self):
        name = Mock()
        self.assertEquals(name.__hash__(), CategoryModel(name).__hash__())
    
    def test_adding_the_same_application(self):
        application = Mock()
        test_object = CategoryModel(Mock())
        
        test_object.add_application(application)
        test_object.add_application(application)
        
        self.assertEquals(ImmutableSet([application]), test_object.get_applications_set())