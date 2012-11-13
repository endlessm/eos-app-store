from startup.auto_updates.endless_downloader import EndlessDownloader
from startup.auto_updates.force_install import ForceInstall
from startup.auto_updates.install_notifier import InstallNotifier
from eos_log import log

class EndlessUpdater():
    
    def __init__(self, endless_downloader=EndlessDownloader(), 
                 force_install=ForceInstall(),
                 install_notifier=InstallNotifier()):
        
        self._endless_downloader = endless_downloader
        self._install_notifier = install_notifier
        
        self._install_notifier.add_listener(
                                    InstallNotifier.USER_RESPONSE, 
                                    lambda: self._handle_user_response(install_notifier, force_install))

    def _handle_user_response(self, install_notifier, force_install):
        log.info("notifying user of updates to install")
        if install_notifier.should_install():
            force_install.install_in_background()
        else: 
            log.info("user refused install")

    def update(self):
        log.info("downloading all updates")
        self._endless_downloader.download_all_packages()
        log.info("updates finished downloading")
        
        self._install_notifier.notify_user()
