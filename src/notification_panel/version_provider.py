import json
import sys

class VersionProvider():
    DEFAULT_VERSION_FILE = "/usr/share/endlessm/version.json"
    
    def __init__(self, version_file=DEFAULT_VERSION_FILE):
        self._version_file = version_file
        self._load_data()
        
    def _load_data(self):
        try:
            with open(self._version_file, "r") as f:
                self._data = json.load(f)
        except:
            print >> sys.stderr, "No file: " + self._version_file
            
    def get_current_version(self):
        try:
            return self._data["version"]
        except KeyError:
            print >> sys.stderr, "No version found in file: " + self.DEFAULT_VERSION_FILE
            return None
    
    def get_server_endpoint(self):
        try:
            return self._data["server_endpoint"]
        except KeyError:
            print >> sys.stderr, "No server endpoint found in file: " + self.DEFAULT_VERSION_FILE
            return None
