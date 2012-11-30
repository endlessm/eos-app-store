import unittest
from mock import Mock #@UnresolvedImport
from startup.auto_updates.latest_version_provider import LatestVersionProvider
import json
from eos_installer import endpoint_provider

class LatestVersionProviderTestCase(unittest.TestCase):
    def setUp(self):
        self._orig_get_endless_url = endpoint_provider.get_endless_url
        
        self._expected_version = "2.1.3"
        content = json.dumps({"version": self._expected_version})
        
        self._mock_web_connection = Mock()
        self._mock_web_connection.get = Mock(return_value=content)
        
        self._test_object = LatestVersionProvider(self._mock_web_connection)
        
    def tearDown(self):
        endpoint_provider.get_endless_url = self._orig_get_endless_url
        
    def test_get_latest_version(self):
        self.assertEquals(self._expected_version, self._test_object.get_latest_version())
        
    def test_get_latest_version_calls_correct_endpoint(self):
        given_endpoint = "this is an endpoint"
        endpoint_provider.get_endless_url = Mock(return_value=given_endpoint)

        self._test_object.get_latest_version()
        
        self._mock_web_connection.get.assert_called_once_with(
                          given_endpoint + "/install/version.json",
                          self._test_object.USERNAME,
                          self._test_object.PASSWORD)
