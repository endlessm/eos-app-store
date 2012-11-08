import unittest
from mock import Mock, call #@UnresolvedImport

from startup.auto_updates.endless_installer import EndlessInstaller

class EndlessInstallerTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._test_object = EndlessInstaller(self._mock_os_util)

    def test_install_all_packages_will_use_dpkg_to_install_all_files_in_the_given_directory(self):
        directory = "this is the given directory"
        self._mock_os_util.execute = Mock()
        
        self._test_object.install_all_packages(directory)

        expected_calls = [ 
                    call(["sudo", "/usr/bin/endless_pre_install.sh"]),
                    call(["sudo", "/usr/bin/endless_install_all_packages.sh", directory]),
                    call(["sudo", "/usr/bin/endless_post_install.sh"])]

        self.assertEquals(expected_calls, self._mock_os_util.execute.call_args_list)

