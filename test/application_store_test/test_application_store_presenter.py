import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
from mock import Mock


class ApplicationStorePresenterTestCase(unittest.TestCase):
    
    def test_show_categories(self):
        view = Mock()
        model = Mock()
        categories = ['Audio']
        model.get_categories = Mock(return_value=categories)
        self._presenter = ApplicationStorePresenter(view, model)
        
        self._presenter.show_categories()
        
        model.get_categories.assert_called_once_with()
        view.show_categories.assert_called_once_with(categories)
    
    def test_show_category(self):
        view = Mock()
        view.show_category = Mock()
        model = Mock()
        category = Mock()
        applications_set = Mock()
        category.get_applications_set = Mock(return_value=applications_set)
        self._presenter = ApplicationStorePresenter(view, model)
        
        self._presenter.show_category(category)
        
        view.show_category.assert_called_once_with(applications_set)