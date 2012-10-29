import os
from xdg.DesktopEntry import DesktopEntry
from sets import ImmutableSet
from application_store.application_store_errors import ApplicationStoreWrappedException

class ApplicationStoreModel():
    def __init__(self, base_dir=''):
        self._base_dir = base_dir

    def get_categories(self):
        categories = Categories()
        try:
            for desktop_filename in os.listdir(self._base_dir):
                desktop_file_path = os.path.join(self._base_dir, desktop_filename)
                if os.path.isfile(desktop_file_path):
                    desktop_entry = DesktopEntry()
                    desktop_entry.parse(desktop_file_path)
                    categories.add_application(desktop_entry)
        except OSError as e:
            raise ApplicationStoreWrappedException(e, 'failed to find app store directory')
        return categories.get_categories_set()


class Categories():
    def __init__(self):
        self.categories = {}
    
    def get_categories_set(self):
        return ImmutableSet(self.categories.values())
    
    def add_application(self, application):
        for category_name in application.getCategories():
            category = self.categories.get(category_name, Category(category_name)) 
            category.add_application(application)
            self.categories[category_name] = category

class Category:
    def __init__(self, name):
        self._name = name
        self._applications = []
    
    def add_application(self, application):
        self._applications.append(application)

    def __eq__(self, other):
        return self._name == other._name
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return self._name.__hash__()