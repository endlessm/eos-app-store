import unittest

from repo_chooser.environment_manager import EnvironmentManager
from repo_chooser.repo_def import RepoDef

class EnvironmentManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = EnvironmentManager()
           
    def test_when_given_demo_password_return_demo(self):
        demo_repo = self._test_object.find_repo(EnvironmentManager.DEMO_PASS)

        self.assertEquals("DEMO ", demo_repo.display_name)
        self.assertEquals("http://apt.endlessdevelopment.com/demo", demo_repo.repo_url)

    def test_when_given_dev_password_return_dev(self):
        dev_repo = self._test_object.find_repo(EnvironmentManager.DEV_PASS)

        self.assertEquals("DEV ", dev_repo.display_name)
        self.assertEquals("http://em-vm-build", dev_repo.repo_url)

    def test_when_given_apt_testing_password_return_apt_testing(self):
        test_repo = self._test_object.find_repo(EnvironmentManager.APT_TESTING_PASS)

        self.assertEquals("APT TESTING ", test_repo.display_name)
        self.assertEquals("http://apt.endlessdevelopment.com/apt_testing", test_repo.repo_url)

    def test_when_given_none_returns_prod(self):
        default_repo = self._test_object.find_repo(None)

        self.assertEquals("", default_repo.display_name)
        self.assertEquals("http://apt.endlessdevelopment.com/updates", default_repo.repo_url)
