import sys
import re

class EndpointProvider():

    DEFAULT_SERVER_ENDPOINT = "apt.endlessm.com"
    DEFAULT_ENDPOINT_FILE = "/usr/share/endlessm/endpoint.txt"
    
    def __init__(self, endpoint_file=DEFAULT_ENDPOINT_FILE):
        self._endpoint_file = endpoint_file
        
    def _load_data(self):
        if not hasattr(self, "_data"):
            try:
                with open(self._endpoint_file, "r") as f:
                    self._data = re.sub("/repository", "", f.read().strip())
            except:
                print >> sys.stderr, "No file: " + self._endpoint_file
    
    def get_server_endpoint(self):
        self._load_data()
        
        if hasattr(self, "_data") and self._data != "":
            return self._data
        else:
            return self.DEFAULT_SERVER_ENDPOINT
