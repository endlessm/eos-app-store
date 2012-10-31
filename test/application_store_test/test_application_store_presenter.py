import unittest
from application_store.application_store_presenter import ApplicationStorePresenter
from mock import Mock


class ApplicationStorePresenterTestCase(unittest.TestCase):
    
    def setUp(self):
        self._view = Mock()
        self._model = Mock()
        self._desktop_presenter = Mock()
        
        self._presenter = ApplicationStorePresenter(self._desktop_presenter, self._view, self._model)
    
    def test_show_categories(self):
        categories = ['Audio']
        self._model.get_categories = Mock(return_value=categories)
        
        self._presenter.show_categories()
        
        self._model.get_categories.assert_called_once_with()
        self._view.show_categories.assert_called_once_with(categories)
    
    def test_show_category(self):
        self._view.show_category = Mock()
        self._model.set_current_category = Mock()
        category = Mock()
        applications_set = Mock()
        category.get_applications_set = Mock(return_value=applications_set)
        
        self._presenter.show_category(category)
        
        self._view.show_category.assert_called_once_with(applications_set)
        self._model.set_current_category.assert_called_once_with(category)
        
    def test_install_application(self):
        self._view.show_category = Mock()
        current_category = Mock()
        self._model.current_category = Mock(return_value=current_category)
        current_application_set = Mock()
        application = Mock()
        current_category.get_applications_set = Mock(return_value=current_application_set)
        
        self._presenter.install_application(application)
        
        self._model.install.assert_called_once_with(application)
        self._view.show_category.assert_called_once_with(current_application_set)
        self._desktop_presenter.refresh_view.assert_called_once_with()
        