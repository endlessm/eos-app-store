import json

from osapps.web_connection import WebConnection
from startup.auto_updates import endpoint_provider

class LatestVersionProvider():
    USERNAME = 'endlessos'
    PASSWORD = 'install'
    
    def __init__(self, web_connection=WebConnection()):
        self._web_connection = web_connection
    
    def get_latest_version(self):
        endpoint = endpoint_provider.get_endless_url() + "/install/version.json"
        response = self._web_connection.get(endpoint, self.USERNAME, self.PASSWORD)
        version = json.loads(response)
        return version["version"]
    
