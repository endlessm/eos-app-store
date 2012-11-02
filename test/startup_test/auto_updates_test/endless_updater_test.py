import unittest
from mock import Mock #@UnresolvedImport
import os

from startup.auto_updates.endless_updater import EndlessUpdater
from startup.auto_updates import endpoint_provider
from startup.auto_updates.install_notifier import InstallNotifier

class EndlessUpdaterTestCase(unittest.TestCase):
    _test_directory = "this is the test directory"
    
    def setUp(self):
        self._mock_endless_downloader = Mock()
        self._mock_endless_installer = Mock()
        self._mock_install_notifier = Mock()
        self._test_object = EndlessUpdater(self._test_directory,
                                           self._mock_endless_downloader, 
                                           self._mock_endless_installer,
                                           self._mock_install_notifier)
        
        self._orig_os_environ = os.environ
        self._orig_endpoint_provider = endpoint_provider.get_current_apt_endpoint
    
    def tearDown(self):
        os.environ = self._orig_os_environ
        endpoint_provider.get_current_apt_endpoint = self._orig_endpoint_provider
    
    def test_download_directory_environment_variable_is_setup(self):
        os.environ = {}
        
        self._test_object.update()

        self.assertEquals(self._test_directory, os.environ["ENDLESS_DOWNLOAD_DIRECTORY"])
    
    def test_endless_endpoint_environment_variable_is_setup(self):
        os.environ = {}
        apt_endpoint = "this is the endpoint"
        endpoint_provider.get_current_apt_endpoint = Mock(return_value=apt_endpoint)
        
        self._test_object.update()

        self.assertEquals(apt_endpoint, os.environ["ENDLESS_ENDPOINT"])
    
    def test_update_first_updates_the_repositories(self):
        self._mock_endless_downloader.update_repositories = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.update_repositories.assert_called_once_with()
        
    def test_update_then_downloads_all_packages(self):
        self._mock_endless_downloader.download_all_packages = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.download_all_packages.assert_called_once_with(self._test_directory)

    def test_when_doing_updates_user_is_notified(self):
        self._mock_install_notifier.notify_user = Mock()
        
        self._test_object.update()
        
        self._mock_install_notifier.notify_user.assert_called_once_with()

    def test_do_not_install_all_packages_until_user_responds(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._test_directory,
                                           self._mock_endless_downloader, 
                                           self._mock_endless_installer,
                                           self._mock_install_notifier)
        
        self._mock_endless_installer.install_all_packages = Mock()
        self._test_object.update()

        self.assertFalse(self._mock_endless_installer.install_all_packages.called, 
                         "Should not have installed all packages")

    def test_when_user_response_that_they_want_to_install_then_install_all_packages(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._test_directory,
                                           self._mock_endless_downloader, 
                                           self._mock_endless_installer,
                                           self._mock_install_notifier)
        
        self._mock_install_notifier.should_install = Mock(return_value=True)
        self._mock_endless_installer.install_all_packages = Mock()
        self._test_object.update()

        self._user_notified_listener()
        
        self.assertTrue(self._mock_endless_installer.install_all_packages.called, 
                         "Should have installed all packages")
        
    def test_when_user_response_that_they_do_not_want_to_install_then_install_all_packages(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._test_directory,
                                           self._mock_endless_downloader, 
                                           self._mock_endless_installer,
                                           self._mock_install_notifier)
        
        self._mock_install_notifier.should_install = Mock(return_value=False)
        self._mock_endless_installer.install_all_packages = Mock()
        self._test_object.update()

        self._user_notified_listener()
        
        self.assertFalse(self._mock_endless_installer.install_all_packages.called, 
                         "Should not have installed all packages")

    def _user_notifier_add_listener(self, *args, **kwargs):
        if args[0] == InstallNotifier.USER_RESPONSE:
            self._user_notified_listener = args[1]
    
    
    
