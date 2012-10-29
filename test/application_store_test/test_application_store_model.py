import unittest
from mock import Mock
from application_store.application_store_model import ApplicationStoreModel


class ApplicationStoreModelTestCase(unittest.TestCase):
    
    def test_get_categories_returns_an_empty_list_when_there_are_no_categories(self):
        self._test_object = ApplicationStoreModel()
        self.assertEquals([], self._test_object.get_categories())