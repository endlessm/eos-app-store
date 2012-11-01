from osapps.os_util import OsUtil
import os
import shutil

class EndlessDownloader():
    def __init__(self, os_util=OsUtil()):
        self._os_util = os_util
    
    def update_repositories(self):
        self._os_util.execute(["sudo", "/usr/bin/endless_update_repositories.sh"])
    
    def download_all_packages(self, download_directory):
        self._clean_out_download_directory(download_directory)
        
        self._os_util.execute(["sudo", "/usr/bin/endless_install_all_packages.sh"])
        
    def _clean_out_download_directory(self, download_directory):
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
        
        for item in os.listdir(download_directory):
            item_to_delete = os.path.join(download_directory, item)
            if os.path.isdir(item_to_delete):
                shutil.rmtree(item_to_delete, False)
            else:
                os.unlink(item_to_delete)