import os
from eos_util.locale_util import LocaleUtil
from desktop_files.desktop_file_utilities import DesktopFileUtilities

class RecommendedSitesProvider(object):
    '''
    This class provides recommended sites based on the locale
    '''

    DEFAULT_SITES_DIRECTORY = '/usr/share/endlessm-sites'

    def __init__(self, directory=DEFAULT_SITES_DIRECTORY, desktop_file_model = DesktopFileUtilities(), locale_util=LocaleUtil()):
        self._desktop_file_model = desktop_file_model
        self._base_dir = locale_util.append_dir_with_current_locale(directory)

    def get_recommended_sites(self):
        links = []
        for desktop_filename in self._desktop_file_model.get_desktop_files(self._base_dir):
            desktop_file_path = os.path.join(self._base_dir, desktop_filename)
            link = self._desktop_file_model.create_model(desktop_file_path, desktop_filename)
            links.append(link)
        links.sort(key= lambda l: l.name())
        return links


