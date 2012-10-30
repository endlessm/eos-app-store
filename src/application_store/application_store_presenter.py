from application_store.application_store_model import ApplicationStoreModel
from application_store.application_store_view import ApplicationStoreView

class ApplicationStorePresenter():
    def __init__(self, view = ApplicationStoreView(), model = ApplicationStoreModel()):
        self._view = view
        self._model = model
        self._view.set_presenter(self)
    
    def show_categories(self):
        self._view.show_categories(self._model.get_categories())

    def show_category(self, category):
        self._view.show_category(category.get_applications_set())