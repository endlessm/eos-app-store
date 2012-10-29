import os
from xdg.DesktopEntry import DesktopEntry
from sets import ImmutableSet

class ApplicationStoreModel():
    def __init__(self, base_dir=''):
        self._base_dir = base_dir

    def get_categories(self):
        categories = []
        for desktop_filename in os.listdir(self._base_dir):
            desktop_file_path = os.path.join(self._base_dir, desktop_filename)
            if os.path.isfile(desktop_file_path):
                desktop_entry = DesktopEntry()
                desktop_entry.parse(desktop_file_path)
                for category in desktop_entry.getCategories():
                    categories.append(category)
        return ImmutableSet(categories)
