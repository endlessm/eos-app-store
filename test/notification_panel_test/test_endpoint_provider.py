import unittest
from osapps.os_util import OsUtil
from notification_panel.endpoint_provider import EndpointProvider

class TestEndpointProvider(unittest.TestCase):
    _filename = "/tmp/endpoint_test_file.txt"
    _server_endpoint = "server endpoint"
    
    def setUp(self):
        with open(self._filename, "w") as f:
            f.write(self._server_endpoint)
        self.test_object = EndpointProvider(self._filename)

    def tearDown(self):
        OsUtil().execute(["rm", "-f", self._filename])
    
    def test_get_server_endpoint_returns_server_endpoint_from_file(self):
        self.assertEquals(self._server_endpoint, self.test_object.get_server_endpoint())

    def test_get_server_endpoint_returns_default_when_file_does_not_exist(self):
        self.test_object = EndpointProvider("fictitious/file/location.txt")
        
        self.assertEquals(EndpointProvider.DEFAULT_SERVER_ENDPOINT, self.test_object.get_server_endpoint())
      
    def test_get_server_endpoint_returns_default_when_server_endpoint_is_not_in_file(self):
        self.tearDown()

        with open(self._filename, "w") as f:
            f.write("")
        self.test_object = EndpointProvider(self._filename)
        
        self.assertEquals(EndpointProvider.DEFAULT_SERVER_ENDPOINT, self.test_object.get_server_endpoint())
        
