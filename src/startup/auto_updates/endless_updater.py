from startup.auto_updates.endless_downloader import EndlessDownloader
from startup.auto_updates.endless_installer import EndlessInstaller
from startup.auto_updates.install_notifier import InstallNotifier
from startup.auto_updates.install_script_executor import InstallScriptExecutor

import os

class EndlessUpdater():
    def __init__(self, install_script_executor=InstallScriptExecutor(),
                 download_directory="/tmp/endless-os-install-directory/",
                 endless_downloader=EndlessDownloader(), 
                 endless_installer=EndlessInstaller(),
                 install_notifier=InstallNotifier()):
        self._install_script_executor = install_script_executor
        self._download_directory = download_directory
        self._endless_downloader = endless_downloader
        self._endless_installer = endless_installer
        self._install_notifier =install_notifier
    
    def update(self):
        os.environ["ENDLESS_DOWNLOAD_DIRECTORY"] = self._download_directory
        
        self._endless_downloader.update_repositories()
        
        self._endless_downloader.download_all_packages(self._download_directory)
        
        self._install_script_executor.execute_preinstall_script()
        if self._install_notifier.notify_user():
            self._endless_installer.install_all_packages()
        self._install_script_executor.execute_postinstall_script()