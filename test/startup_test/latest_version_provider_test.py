import unittest
from mock import Mock #@UnresolvedImport
from startup.update_checker import LatestVersionProvider

class LatestVersionProviderTestCase(unittest.TestCase):
    def test_(self):
        test_object = LatestVersionProvider()
        test_object.get_latest_version()
        