import unittest
from mock import Mock #@UnresolvedImport
from startup.latest_version_provider import LatestVersionProvider


class LatestVersionProviderTestCase(unittest.TestCase):
    def test_get_latest_version(self):
#        mock_requestor = Mock()
#        mock_requestor.download_version = Mock(return_value="{\"version\":\"1.0.0\"}")
        test_object = LatestVersionProvider()
        test_object._download_json = Mock(return_value="{\"version\":\"1.0.0\"}")
        self.assertEquals("1.0.0", test_object.get_latest_version())
        