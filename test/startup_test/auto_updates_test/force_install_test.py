import unittest

from mock import Mock

from startup.auto_updates.force_install import ForceInstall

class ForceInstallTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_endless_installer = Mock()
        self._mock_force_install_checker = Mock()

        self._test_object = ForceInstall(self._mock_force_install_checker, self._mock_endless_installer)

    def test_install_all_packages_when_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
    
        self.assertTrue(self._mock_endless_installer.install_all_packages.called)

    def test_dont_install_all_packages_when_no_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()
    
        self.assertFalse(self._mock_endless_installer.install_all_packages.called)
