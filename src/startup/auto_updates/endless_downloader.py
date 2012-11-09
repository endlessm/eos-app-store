import os

from startup.auto_updates import endpoint_provider
from startup.auto_updates.file_synchronizer import FileSynchronizer
from startup.auto_updates.file_downloader import FileDownloader

class EndlessDownloader():
    INDEX_FILE = "files.txt"
    
    def __init__(self, file_downloader=FileDownloader(), file_synchronizer=FileSynchronizer()):
        self._file_downloader = file_downloader
        self._file_synchronizer = file_synchronizer
    
    def download_all_packages(self, download_directory):
        local_file_list = os.listdir(download_directory)
        endpoint = endpoint_provider.get_endless_url()

        remote_file_list = self._file_downloader.download_file(os.path.join(endpoint, self.INDEX_FILE))
        files_to_download = self._file_synchronizer.files_to_download(local_file_list, remote_file_list)
        for remote_file, expected_md5 in files_to_download:
            file_content = self._file_downloader.download_file(endpoint + "/" + remote_file, expected_md5)

            with open(os.path.join(download_directory, remote_file), "w") as local_file:
                local_file.write(file_content)

        with open(os.path.join(download_directory, self.INDEX_FILE), "w") as f:
            f.write(remote_file_list)



