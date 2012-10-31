import os
from xdg.DesktopEntry import DesktopEntry
from sets import ImmutableSet
from application_store.application_store_errors import ApplicationStoreWrappedException
from application_store.application_model import ApplicationModel
from application_store.category_model import CategoryModel
from application_store.categories_model import CategoriesModel
from application_store.installed_applications_model import InstalledApplicationsModel

class ApplicationStoreModel():
    def __init__(self, base_dir='', installed_applications_model = InstalledApplicationsModel()):
        self._base_dir = base_dir
        self._current_category = None
        self._installed_applications_model = installed_applications_model
        self._installed_applications_model.set_data_dir(self._base_dir)

    def current_category(self):
        return self._current_category

    def set_current_category(self, category):
        self._current_category = category

    def get_categories(self):
        return self._refresh().get_categories_set()

    def get_application(self, file_path, filename):
        desktop_entry = DesktopEntry()
        desktop_entry.parse(file_path)
        return ApplicationModel(file_path, filename, desktop_entry.getCategories())
    
    def install(self, application):
        self._installed_applications_model.install(application.id())
        self._refresh()

    def _refresh(self):
        categories = CategoriesModel()
        try:
            for desktop_filename in self._desktop_files():                    
                desktop_file_path = os.path.join(self._base_dir, desktop_filename)
                if not self._installed_applications_model.is_installed(desktop_filename):
                    application = self.get_application(desktop_file_path, desktop_filename)
                    categories.add_application(application)
        except OSError as e:
            raise ApplicationStoreWrappedException(e, 'failed to find app store directory')
        if self._current_category is not None:
            self._current_category = categories.get_updated_category(self._current_category)
        return categories

    def _desktop_files(self):
        desktop_files = []
        for filename in os.listdir(self._base_dir):
            if filename.endswith('.desktop'):
                desktop_files.append(filename)
        return desktop_files
