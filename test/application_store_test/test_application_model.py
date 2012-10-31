import unittest
from mock import Mock, call
from application_store.application_model import ApplicationModel


class ApplicationModelTestCase(unittest.TestCase):
    def test_a_model_with_the_same_application_id_is_equal(self):
        id = Mock()
        self.assertEquals(ApplicationModel(Mock(), id, None), ApplicationModel(Mock(), id, ["Video"]))
    
    def test_a_model_with_a_different_id_is_not_equal(self):
        self.assertNotEqual(ApplicationModel(Mock(), Mock(), None), ApplicationModel(Mock(), Mock(), None))
    
    def test_the_hash_is_based_on_the_id(self):
        id = Mock()
        self.assertEquals(id.__hash__(), ApplicationModel(Mock(), id, None).__hash__())
    
    def test_categories_returns_the_list_of_categories_the_application_has(self):
        categories = Mock()
        self.assertEquals(categories, ApplicationModel(Mock(), Mock(), categories).get_categories())
        
    def test_application_visits_all_categories(self):
        test_object = ApplicationModel(Mock(), 'id', ["Audio", "Video"])
        visitor = Mock()
        
        test_object.visit_categories(visitor)
        
        calls = []
        calls.append(call("Audio", test_object))
        calls.append(call("Video", test_object))
        visitor.assert_has_calls(calls, any_order=True)