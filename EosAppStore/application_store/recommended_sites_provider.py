import os
from EosAppStore.eos_util.locale_util import LocaleUtil
from EosAppStore.eos_util import path_util
from EosAppStore.desktop_files.desktop_file_utilities import DesktopFileUtilities
from EosAppStore.application_store.installed_applications_model import InstalledApplicationsModel

class RecommendedSitesProvider(object):
    '''
    This class provides recommended sites based on the locale
    '''

    def __init__(self, directory=path_util.DEFAULT_SITES_DIRECTORY, desktop_file_model = DesktopFileUtilities(), locale_util=LocaleUtil()):
        self._desktop_file_model = desktop_file_model
        #self._base_dir = locale_util.append_dir_with_current_locale(directory)
        self._base_dir = directory
        self._installed_links_model = InstalledApplicationsModel()

    def get_recommended_sites(self):
        links = []
        for desktop_filename in self._desktop_file_model.get_desktop_files(self._base_dir):
            desktop_file_path = os.path.join(self._base_dir, desktop_filename)
            if desktop_filename.startswith(path_util.EOS_LINK_PREFIX) and not self._installed_links_model.is_installed(desktop_filename):
                link = self._desktop_file_model.create_model(desktop_file_path, desktop_filename)
                links.append(link)
        links.sort(key= lambda l: l.name())
        return links


