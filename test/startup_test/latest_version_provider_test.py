import unittest
from mock import Mock #@UnresolvedImport
from startup.latest_version_provider import LatestVersionProvider
import json
from startup import endpoint_provider

class LatestVersionProviderTestCase(unittest.TestCase):
    def setUp(self):
        content = json.dumps({"version": "1.0.0"})
        
        mock_response = Mock()
        mock_response.read = Mock(return_value=content)
        
        self._mock_web_connection = Mock()
        self._mock_web_connection.get = Mock(return_value=mock_response)
        
        self._test_object = LatestVersionProvider(self._mock_web_connection)
        
    def test_get_latest_version(self):
        self.assertEquals("1.0.0", self._test_object.get_latest_version())
        
    def test_get_latest_version_calls_correct_endpoint(self):
        self._test_object.get_latest_version()
        
        self._mock_web_connection.get.assert_called_once_with(
                          self._test_object._endpoint,
                          self._test_object.USERNAME,
                          self._test_object.PASSWORD)

    def test_endpoint_is_taken_from_endpoint_provider(self):
        given_endpoint = "this is an endpoint"
        orig = endpoint_provider.get_current_apt_endpoint
        endpoint_provider.get_current_apt_endpoint = Mock(return_value=given_endpoint)
        
        test_object = LatestVersionProvider()
        
        self.assertEquals(given_endpoint, test_object._endpoint)
        
        endpoint_provider.get_current_apt_endpoint = orig
