import json
import urllib2

class LatestVersionProvider():
    
    def __init__(self):
        pass
    
    def get_latest_version(self):
        version_json = self._download_json()
        version = json.loads(version_json)
        return version["version"]
    
    def _download_json(self):     
        response = urllib2.urlopen("http://apt.endlessm.com/version.json")
        return response.read()