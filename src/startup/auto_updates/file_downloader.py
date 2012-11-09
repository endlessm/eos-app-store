import md5

from osapps.web_connection import WebConnection

class FileDownloader(object):
    MAX_RETRIES = 2
    
    def __init__(self, web_connection = WebConnection()):
        self._web_connection = web_connection
    
    def download_file(self, location, expected_md5 = None):
        current_attempt = 1
        
        while current_attempt <= self.MAX_RETRIES:
            file_content = self._web_connection.get(location)

            if not expected_md5:
                return file_content

            md5sum = md5.new(file_content).hexdigest()
            if md5sum == expected_md5:
                return file_content
            
            current_attempt += 1
         
        raise Exception("Could not download file: ", location)
