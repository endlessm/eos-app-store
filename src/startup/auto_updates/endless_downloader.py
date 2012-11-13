import os

from startup.auto_updates import endpoint_provider
from startup.auto_updates.file_synchronizer import FileSynchronizer
from startup.auto_updates.file_downloader import FileDownloader

import re

class EndlessDownloader():
    DEFAULT_DOWNLOAD_DIRECTORY = "/var/lib/endless/packages"

    INDEX_FILE = "files.txt"
    
    def __init__(self, file_downloader=FileDownloader(), 
            file_synchronizer=FileSynchronizer(), 
            download_directory=DEFAULT_DOWNLOAD_DIRECTORY):
        self._file_downloader = file_downloader
        self._file_synchronizer = file_synchronizer
        self._download_directory = download_directory
    
    def download_all_packages(self):
        local_file_list = os.listdir(self._download_directory)
        local_file_list.sort()
        endpoint = endpoint_provider.get_endless_url()

        mirror_url = endpoint + "/mirror/"

        remote_file_list = self._file_downloader.download_file(mirror_url + self.INDEX_FILE)
        files_to_download = self._file_synchronizer.files_to_download(local_file_list, remote_file_list)
        for remote_file, expected_md5 in files_to_download:
            if "%" in remote_file:
                remote_file = re.sub("%", "%25", remote_file)
            file_content = self._file_downloader.download_file(mirror_url + remote_file, expected_md5)

            with open(os.path.join(self._download_directory, remote_file), "w") as local_file:
                local_file.write(file_content)

        with open(os.path.join(self._download_directory, self.INDEX_FILE), "w") as f:
            f.write(remote_file_list)



