import unittest
from mock import Mock #@UnresolvedImport

import os
from startup.endless_installer import EndlessInstaller

class EndlessInstallerTestCase(unittest.TestCase):
    _test_directory = "this is the download directory"
    
    def setUp(self):
        self._mock_os_util = Mock()
        self._test_object = EndlessInstaller(self._mock_os_util)

    def test_install_all_packages_will_use_dpkg_to_install_all_files_in_the_given_directory(self):
        self._mock_os_util.execute = Mock()
        
        self._test_object.install_all_packages(self._test_directory)
        
        self._mock_os_util.execute.assert_called_once_with(
                                    ["sudo", "/usr/bin/endless_install_all_packages.sh"])
