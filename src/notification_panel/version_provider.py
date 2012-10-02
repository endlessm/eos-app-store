import json
import sys

class VersionProvider():

    DEFAULT_SERVER_ENDPOINT = "apt.endlessm.com"
    DEFAULT_VERSION_FILE = "/usr/share/endlessm/version.json"
    
    def __init__(self, version_file=DEFAULT_VERSION_FILE):
        self._version_file = version_file
        
    def _load_data(self):
        if not hasattr(self, "_data"):
            try:
                with open(self._version_file, "r") as f:
                    self._data = json.load(f)
            except:
                print >> sys.stderr, "No file: " + self._version_file
            
    def get_current_version(self):
        self._load_data()
        
        try:
            return self._data["version"]
        except KeyError:
            print >> sys.stderr, "No version found in file: " + self.DEFAULT_VERSION_FILE
            return None
    
    def get_server_endpoint(self):
        self._load_data()
        
        if hasattr(self, "_data") and "server_endpoint" in self._data:
            return self._data["server_endpoint"]
        else:
            return self.DEFAULT_SERVER_ENDPOINT
