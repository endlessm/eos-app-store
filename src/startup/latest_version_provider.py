import json

from osapps.web_connection import WebConnection
from startup import endpoint_provider

class LatestVersionProvider():
    USERNAME = 'endlessos'
    PASSWORD = 'install'
    
    def __init__(self, web_connection=WebConnection()):
        self._web_connection = web_connection
        self._endpoint = endpoint_provider.get_current_apt_endpoint()
    
    def get_latest_version(self):
        response = self._web_connection.get(self._endpoint, self.USERNAME, self.PASSWORD)
        version_json = response.read()
        version = json.loads(version_json)
        return version["version"]
    