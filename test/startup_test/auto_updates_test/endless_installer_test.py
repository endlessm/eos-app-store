import unittest
from mock import Mock, call #@UnresolvedImport

from startup.auto_updates.endless_installer import EndlessInstaller
from startup.auto_updates import endpoint_provider

class EndlessInstallerTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._mock_force_install_checker = Mock()

        self._test_object = EndlessInstaller(self._mock_os_util, self._mock_force_install_checker)

        self._orig_endpoint_provider = endpoint_provider.reset_url

    def tearDown(self):
        endpoint_provider.reset_url = self._orig_endpoint_provider

    def test_install_all_packages_will_use_dpkg_to_install_all_files_in_the_given_directory(self):
        directory = "this is the given directory"
        self._mock_os_util.execute = Mock()
        
        self._test_object.install_all_packages(directory)

        expected_calls = [ 
                    call(["sudo", "/usr/bin/endless_pre_install.sh"]),
                    call(["sudo", "/usr/bin/endless_install_all_packages.sh", directory]),
                    call(["sudo", "/usr/bin/endless_post_install.sh"]),
                    call(["sudo", "/sbin/shutdown", "-r", "now"])]

        self.assertEquals(expected_calls, self._mock_os_util.execute.call_args_list)

    def test_installing_all_packages_will_reset_the_endpoint(self):
        endpoint_provider.reset_url = Mock()

        self._test_object.install_all_packages(Mock())

        self.assertTrue(endpoint_provider.reset_url.called)

    def test_installing_all_packages_should_inform_the_install_checker_that_the_install_was_accomplished(self):
        self._test_object.install_all_packages(Mock())

        self.assertTrue(self._mock_force_install_checker.install_accomplished.called)

