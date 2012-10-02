import unittest
from notification_panel.version_provider import VersionProvider
import json
from osapps.os_util import OsUtil

class TestVersionProvider(unittest.TestCase):
    _filename = "/tmp/version.json"
    _current_version = "endless os version"
    _server_endpoint = "server endpoint"
    
    def setUp(self):
        file_data = {
                          "version":self._current_version,
                          "server_endpoint":self._server_endpoint
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)

    def tearDown(self):
        OsUtil().execute(["rm", "-f", self._filename])
    
    def test_get_current_version_returns_version_from_file(self):
        self.assertEquals(self._current_version, self.test_object.get_current_version())
        
    def test_get_current_version_returns_None_when_version_is_not_in_file(self):
        self.tearDown()
        file_data = {
                          "server_endpoint":self._server_endpoint
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)
        
        self.assertEquals(None, self.test_object.get_current_version())
    
    def test_get_server_endpoint_returns_server_endpoint_from_file(self):
        self.assertEquals(self._server_endpoint, self.test_object.get_server_endpoint())

    def test_get_server_endpoint_returns_default_when_file_does_not_exist(self):
        self.test_object = VersionProvider("fictitious/file/location.txt")
        
        self.assertEquals(VersionProvider.DEFAULT_SERVER_ENDPOINT, self.test_object.get_server_endpoint())
      
    def test_get_server_endpoint_returns_default_when_server_endpoint_is_not_in_file(self):
        self.tearDown()
        file_data = {
                          "version":self._current_version
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)
        
        self.assertEquals(VersionProvider.DEFAULT_SERVER_ENDPOINT, self.test_object.get_server_endpoint())
        
