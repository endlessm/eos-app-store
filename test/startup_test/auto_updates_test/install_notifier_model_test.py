import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier_model import InstallNotifierModel

class InstallNotifierModelTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = InstallNotifierModel()
    
    def test_(self):
        assert self._test_object.should_install()