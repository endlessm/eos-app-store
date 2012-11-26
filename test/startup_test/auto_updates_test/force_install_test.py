import unittest

from mock import Mock

from startup.auto_updates.force_install import ForceInstall
from eos_installer.endless_downloader import EndlessDownloader
from eos_installer import endpoint_provider

class ForceInstallTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_endless_installer = Mock()
        self._mock_force_install_checker = Mock()
        self._mock_force_install_ui = Mock()
        self._mock_os_util = Mock()

        self._test_object = ForceInstall(self._mock_force_install_checker, 
                self._mock_endless_installer, 
                self._mock_force_install_ui,
                self._mock_os_util)

        self._orig_endpoint_provider = endpoint_provider.reset_url
        endpoint_provider.reset_url = Mock()

    def tearDown(self):
        endpoint_provider.reset_url = self._orig_endpoint_provider

    def test_install_all_packages_when_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
        self._test_object._thread.join()
    
        self.assertTrue(self._mock_endless_installer.install_all_packages.called)

    def test_dont_install_all_packages_when_no_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()
    
        self.assertFalse(self._mock_endless_installer.install_all_packages.called)

    def test_launch_ui_when_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
        self._test_object._thread.join()

        self.assertTrue(self._mock_force_install_ui.launch_ui.called)

    def test_dont_launch_ui_when_no_force_install(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()

        self.assertFalse(self._mock_force_install_ui.launch_ui.called)

    def test_if_should_force_install_and_executing_then_reset_the_endpoint(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
        self._test_object._thread.join()

        self.assertTrue(endpoint_provider.reset_url.called)

    def test_if_should_force_install_and_executing_then_inform_the_install_checker_that_the_install_was_accomplished(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
        self._test_object._thread.join()

        self.assertTrue(self._mock_force_install_checker.install_accomplished.called)

    def test_if_should_force_install_and_executing_then_restart(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=True)

        self._test_object.execute()
        self._test_object._thread.join()

        self._mock_os_util.execute.assert_called_once_with(["sudo", "/sbin/shutdown", "-r", "now"])

    def test_if_should_not_force_install_and_executing_then_dont_reset_the_endpoint(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()

        self.assertFalse(endpoint_provider.reset_url.called)

    def test_if_should_not_force_install_and_executing_then_inform_the_install_checker_that_the_install_was_accomplished(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()

        self.assertFalse(self._mock_force_install_checker.install_accomplished.called)

    def test_if_should_not_force_install_and_executing_then_dont_restart(self):
        self._mock_force_install_checker.should_force_install = Mock(return_value=False)

        self._test_object.execute()

        self.assertFalse(self._mock_os_util.execute.called)

