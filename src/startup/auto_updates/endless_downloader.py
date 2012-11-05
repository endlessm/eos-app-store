from osapps.os_util import OsUtil
import os
import shutil

from osapps.web_connection import WebConnection
from startup.auto_updates import endpoint_provider
from startup.auto_updates.file_synchronizer import FileSynchronizer

class EndlessDownloader():
    def __init__(self, web_connection=WebConnection(), file_synchronizer=FileSynchronizer()):
		 self._web_connection = web_connection
		 self._file_synchronizer = file_synchronizer
    
    def download_all_packages(self, download_directory):
        with open(os.path.join(download_directory, "files.txt"), "r") as f:
            local_file_list = f.read()
        endpoint = endpoint_provider.get_current_apt_endpoint()

        remote_file_list = self._web_connection.get(endpoint + "/files.txt")
        files_to_download = self._file_synchronizer.files_to_download(local_file_list, remote_file_list)
        for remote_file in files_to_download:
            file_content = self._web_connection.get(endpoint + "/" + remote_file)
            with open(os.path.join(download_directory, remote_file), "w") as local_file:
                local_file.write(file_content)

