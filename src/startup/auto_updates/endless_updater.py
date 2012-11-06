from startup.auto_updates.endless_downloader import EndlessDownloader
from startup.auto_updates.endless_installer import EndlessInstaller
from startup.auto_updates.install_notifier import InstallNotifier
from startup.auto_updates import endpoint_provider

import os

class EndlessUpdater():
    def __init__(self, download_directory="/tmp/endless-os-install-directory/",
                 endless_downloader=EndlessDownloader(), 
                 endless_installer=EndlessInstaller(),
                 install_notifier=InstallNotifier()):
        self._download_directory = download_directory
        self._endless_downloader = endless_downloader
        self._install_notifier =install_notifier
        self._install_notifier.add_listener(InstallNotifier.USER_RESPONSE, 
                                lambda: self._handle_user_response(install_notifier, endless_installer))

    def _handle_user_response(self, install_notifier, endless_installer):
        if install_notifier.should_install():
            endless_installer.install_all_packages(self._download_directory)

    
    def update(self):
        self._endless_downloader.download_all_packages(self._download_directory)
        
        self._install_notifier.notify_user()

