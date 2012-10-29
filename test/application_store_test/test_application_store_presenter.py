import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
from mock import Mock


class ApplicationStorePresenterTestCase(unittest.TestCase):
    
    def test_show_categories(self):
        view = Mock()
        model = Mock()
        categories = ['Audio']
        model.get_categories = Mock(return_value=categories)
        self._test_object = ApplicationStorePresenter(view, model)
        
        self._test_object.show_categories()
        
        model.get_categories.assert_called_once_with()
        view.show_categories.assert_called_once_with(categories)