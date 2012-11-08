import unittest

from startup.auto_updates import endpoint_provider

class EndpointProviderTestCase(unittest.TestCase):
    def test_(self):
        self.assertEqual("", endpoint_provider.get_current_apt_endpoint())
