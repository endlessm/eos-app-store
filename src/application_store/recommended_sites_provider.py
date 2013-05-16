import os
from eos_util.locale_util import LocaleUtil
from desktop_files.desktop_file_utilities import DesktopFileUtilities

class RecommendedSitesProvider(object):
    '''
    This class provides recommended sites based on the locale
    '''

    DEFAULT_SITES_DIRECTORY = os.environ["XDG_DATA_DIRS"].split(":")[0] + '/applications'
    EOS_LINK_PREFIX = 'eos-link-'

    def __init__(self, directory=DEFAULT_SITES_DIRECTORY, desktop_file_model = DesktopFileUtilities(), locale_util=LocaleUtil()):
        self._desktop_file_model = desktop_file_model
        #self._base_dir = locale_util.append_dir_with_current_locale(directory)
        self._base_dir = directory

    def get_recommended_sites(self):
        links = []
        for desktop_filename in self._desktop_file_model.get_desktop_files(self._base_dir):
            desktop_file_path = os.path.join(self._base_dir, desktop_filename)
            if desktop_filename.startswith(self.EOS_LINK_PREFIX):
                link = self._desktop_file_model.create_model(desktop_file_path, desktop_filename)
                links.append(link)
        links.sort(key= lambda l: l.name())
        return links


