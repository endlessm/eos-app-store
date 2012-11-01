import unittest
from mock import Mock #@UnresolvedImport
import os

from startup.endless_updater import EndlessUpdater

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
    
    def tearDown(self):
        os.environ = self._orig_os_environ
    
    def test_correct_environment_variable_is_setup(self):
        os.environ = {}
        
        self._test_object.update()

        self.assertEquals(self._test_directory, os.environ["ENDLESS_DOWNLOAD_DIRECTORY"])
    
    def test_update_first_updates_the_repositories(self):
        self._mock_endless_downloader.update_repositories = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.update_repositories.assert_called_once_with()
        
    def test_update_then_downloads_all_packages(self):
        self._mock_endless_downloader.download_all_packages = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.download_all_packages.assert_called_once_with(self._test_directory)

    def test_if_user_is_ok_with_doing_updates_then_install_all_the_downloaded_packages(self):
        self._mock_install_notifier.notify_user = Mock(return_value=True)
        self._mock_endless_installer.install_all_packages = Mock()
        
        self._test_object.update()
        
        self._mock_endless_installer.install_all_packages.assert_called_once_with()

    def test_if_user_is_not_ok_with_doing_updates_then_dont_install_all_the_downloaded_packages(self):
        self._mock_install_notifier.notify_user = Mock(return_value=False)
        self._mock_endless_installer.install_all_packages = Mock()
        
        self._test_object.update()
        
        self.assertFalse(self._mock_endless_installer.install_all_packages.called, 
                         "Should not have installed all packages")

