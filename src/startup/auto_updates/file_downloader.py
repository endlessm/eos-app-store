import md5

from eos_log import log
from osapps.web_connection import WebConnection

class FileDownloader(object):
    MAX_RETRIES = 2
    
    def __init__(self, web_connection = WebConnection()):
        self._web_connection = web_connection
    
    def download_file(self, location, expected_md5 = None):
        current_attempt = 1
        
        while current_attempt <= self.MAX_RETRIES:
            log.info("downloading %s -- attempt %d" % (location, current_attempt))
            file_content = self._web_connection.get(location)

            if not expected_md5:
                return file_content

            md5sum = md5.new(file_content).hexdigest()
            if md5sum == expected_md5:
                return file_content
            else:
                log.error("downloading failed b/c of bad md5sum... trying again")
            
            current_attempt += 1
         
        raise Exception("Could not download file: ", location)
