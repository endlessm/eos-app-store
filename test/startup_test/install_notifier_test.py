import unittest
from startup.install_notifier import InstallNotifier

class InstallNotifierTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = InstallNotifier()
    
    def test_(self):
        assert self._test_object.notify_user()


