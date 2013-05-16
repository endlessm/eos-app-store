import os
from application_store.application_store_errors import ApplicationStoreWrappedException
from application_store.categories_model import CategoriesModel
from application_store.installed_applications_model import InstalledApplicationsModel
from desktop_files.desktop_file_utilities import DesktopFileUtilities
from eos_log import log

class ApplicationStoreModel():
    DEFAULT_APP_STORE_DIRECTORY = os.environ["XDG_DATA_DIRS"].split(":")[0] + '/applications'
    EOS_APP_PREFIX = 'eos-app-'

    def __init__(self, directory=DEFAULT_APP_STORE_DIRECTORY, installed_apps_dir=os.path.expanduser("~/.endlessm"), installed_applications_model = InstalledApplicationsModel()):
        self._base_dir = directory
        self._current_category = None
        self._installed_applications_model = installed_applications_model
        self._installed_applications_model.set_data_dir(installed_apps_dir)

    def current_category(self):
        return self._current_category

    def set_current_category(self, category):
        self._current_category = category

    def get_categories(self):
        return self._refresh().get_categories_set()

    def install(self, application):
        self._installed_applications_model.install(application.id())
        self._refresh()

    def _refresh(self):
        categories = CategoriesModel()
        files_model = DesktopFileUtilities()
        try:
            for desktop_filename in files_model.get_desktop_files(self._base_dir):                    
                desktop_file_path = os.path.join(self._base_dir, desktop_filename)
                if desktop_filename.startswith(self.EOS_APP_PREFIX) and not self._installed_applications_model.is_installed(desktop_filename):
                    application = files_model.create_model(desktop_file_path, desktop_filename)
                    categories.add_application(application)
        except OSError as e:
            log.error('oserror = ' + str(e))
            raise ApplicationStoreWrappedException(e, 'failed to find app store directory')
        if self._current_category is not None:
            self._current_category = categories.get_updated_category(self._current_category)
        return categories
