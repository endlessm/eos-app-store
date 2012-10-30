import os
from xdg.DesktopEntry import DesktopEntry
from sets import ImmutableSet
from application_store.application_store_errors import ApplicationStoreWrappedException
from application_store.application_model import ApplicationModel
from application_store.category_model import CategoryModel
from application_store.categories_model import CategoriesModel

class ApplicationStoreModel():
    def __init__(self, base_dir=''):
        self._base_dir = base_dir

    def get_categories(self):
        categories = CategoriesModel()
        try:
            for desktop_filename in os.listdir(self._base_dir):
                desktop_file_path = os.path.join(self._base_dir, desktop_filename)
                if os.path.isfile(desktop_file_path):
                    application = self.get_application(desktop_file_path)
                    categories.add_application(application)
        except OSError as e:
            raise ApplicationStoreWrappedException(e, 'failed to find app store directory')
        return categories.get_categories_set()

    def get_application(self, file_path):
        desktop_entry = DesktopEntry()
        desktop_entry.parse(file_path)
        return ApplicationModel(file_path, desktop_entry.getCategories())