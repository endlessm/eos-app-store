import unittest
from mock import Mock #@UnresolvedImport

from startup.endless_updater import EndlessUpdater

class EndlessUpdaterTestCase(unittest.TestCase):
    _test_directory = "this is the test directory"
    
    def setUp(self):
        self._mock_endless_downloader = Mock()
        self._mock_endless_installer = Mock()
        self._test_object = EndlessUpdater(self._test_directory, 
                                           self._mock_endless_downloader, 
                                           self._mock_endless_installer)
    
    def test_update_first_updates_the_repositories(self):
        self._mock_endless_downloader.update_repositories = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.update_repositories.assert_called_once_with()
        
    def test_update_then_downloads_all_packages(self):
        self._mock_endless_downloader.download_all_packages = Mock()
        
        self._test_object.update()
        
        self._mock_endless_downloader.download_all_packages.assert_called_once_with(self._test_directory)

    def test_update_then_installs_all_the_downloaded_packages(self):
        self._mock_endless_installer.install_all_packages = Mock()
        
        self._test_object.update()
        
        self._mock_endless_installer.install_all_packages.assert_called_once_with(self._test_directory)

#    def test_update_updates_the_repositories_downloads_packages_and_installs_them(self):
#        update_repositories = MagicMock()
#        download_all_packages = MagicMock()
#        install_all_packages = MagicMock()
#        
#        self._mock_endless_downloader.update_repositories = update_repositories
#        self._mock_endless_downloader.download_all_packages = download_all_packages
#        self._mock_endless_installer.install_all_packages = install_all_packages
#
#        parent_mock = MagicMock()
#        parent_mock.update_repositories = update_repositories
#        parent_mock.download_all_packages = download_all_packages
#        parent_mock.install_all_packages = install_all_packages
#        
#        self._test_object.update()
#        
#        expected_calls = [call.update_repositories(), 
#                          call.download_all_packages(self._test_directory), 
#                          call.install_all_packages(self._test_directory)]
#        
#        self.assertEquals(expected_calls, parent_mock.mock_calls)