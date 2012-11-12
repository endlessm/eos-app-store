from startup.auto_updates.endless_downloader import EndlessDownloader
from startup.auto_updates.endless_installer import EndlessInstaller
from startup.auto_updates.install_notifier import InstallNotifier
from eos_log import log

class EndlessUpdater():
    DEFAULT_DOWNLOAD_DIRECTORY = "/var/lib/endless/packages"
    
    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIRECTORY,
                 endless_downloader=EndlessDownloader(), 
                 endless_installer=EndlessInstaller(),
                 install_notifier=InstallNotifier()):
        
        self._download_directory = download_directory
        self._endless_downloader = endless_downloader
        self._install_notifier = install_notifier
        
        self._install_notifier.add_listener(
                                    InstallNotifier.USER_RESPONSE, 
                                    lambda: self._handle_user_response(install_notifier, endless_installer))

    def _handle_user_response(self, install_notifier, endless_installer):
        log.info("notifying user of updates to install")
        if install_notifier.should_install():
            endless_installer.install_all_packages(self._download_directory)
        else: 
            log.info("user refused install")

    def update(self):
        log.info("downloading all updates")
        self._endless_downloader.download_all_packages(self._download_directory)
        log.info("updates finished downloading")
        
        self._install_notifier.notify_user()
