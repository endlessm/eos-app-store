import unittest
import os.path

from repo_chooser.environment_manager import EnvironmentManager

from eos_installer import endpoint_provider

class EnvironmentManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = EnvironmentManager()

        if os.path.exists(os.path.expanduser("~/.endlessm/mirror")):
            os.unlink(os.path.expanduser("~/.endlessm/mirror"))

    def test_setting_prod_password_sets_correct_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.PROD_PASS)

        self.assertEquals("http://apt.endlessdevelopment.com/updates", endpoint_provider.get_endless_url())

    def test_setting_prod_password_sets_correct_current_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.PROD_PASS)

        self.assertEquals("", self._test_object.get_current_repo())

    def test_setting_demo_password_sets_correct_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEMO_PASS)

        self.assertEquals("http://apt.endlessdevelopment.com/demo", endpoint_provider.get_endless_url())

    def test_setting_demo_password_sets_correct_current_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEMO_PASS)

        self.assertEquals("DEMO ", self._test_object.get_current_repo())
           
    def test_setting_dev_password_sets_correct_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEV_PASS)

        self.assertEquals("http://em-vm-build", endpoint_provider.get_endless_url())

    def test_setting_dev_password_sets_correct_current_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEV_PASS)

        self.assertEquals("DEV ", self._test_object.get_current_repo())

    def test_setting_testing_password_sets_correct_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.APT_TESTING_PASS)

        self.assertEquals("http://apt.endlessdevelopment.com/apt_testing", endpoint_provider.get_endless_url())

    def test_setting_testing_password_sets_correct_current_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.APT_TESTING_PASS)

        self.assertEquals("APT TESTING ", self._test_object.get_current_repo())

    def test_setting_bad_password_sets_prod_current_endpoint(self):
        self._test_object.set_current_repo("bad password")

        self.assertEquals("", self._test_object.get_current_repo())

    def test_setting_bad_password_sets_prod_endpoint(self):
        self._test_object.set_current_repo("bad password")

        self.assertEquals("http://apt.endlessdevelopment.com/updates", endpoint_provider.get_endless_url())

    def test_setting_bad_password_after_good_demo_password_sets_prod_current_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEMO_PASS)
        self._test_object.set_current_repo("bad password")

        self.assertEquals("", self._test_object.get_current_repo())

    def test_when_endpoint_from_endpoint_provider_is_bad_return_prod_url(self):
        with open(os.path.expanduser("~/.endlessm/mirror"), "w") as f:
            f.write("blah")

        self.assertEquals("", self._test_object.get_current_repo())

    def test_setting_bad_password_after_good_demo_password_sets_prod_endpoint(self):
        self._test_object.set_current_repo(EnvironmentManager.DEMO_PASS)
        self._test_object.set_current_repo("bad password")

        self.assertEquals("http://apt.endlessdevelopment.com/updates", endpoint_provider.get_endless_url())

