from startup.endless_downloader import EndlessDownloader
from startup.endless_installer import EndlessInstaller


class EndlessUpdater():
    def __init__(self, download_directory="/tmp/endless-os-install-directory/", 
                 endless_downloader=EndlessDownloader(), 
                 endless_installer=EndlessInstaller()):
        self._download_directory = download_directory
        self._endless_downloader = endless_downloader
        self._endless_installer = endless_installer
    
    def update(self):
        self._endless_downloader.update_repositories()
        self._endless_downloader.download_all_packages(self._download_directory)
        self._endless_installer.install_all_packages(self._download_directory)