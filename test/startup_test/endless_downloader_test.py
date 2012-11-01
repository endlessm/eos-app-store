import unittest
from mock import Mock #@UnresolvedImport

import shutil
import os
from startup.endless_downloader import EndlessDownloader

class EndlessDownloaderTestCase(unittest.TestCase):
    _test_directory = "/tmp/updater_test_dir"
    
    def setUp(self):
        shutil.rmtree(self._test_directory, True)
        os.makedirs(self._test_directory)
        
        self._mock_os_util = Mock()
        self._test_object = EndlessDownloader(self._mock_os_util)

    def test_update_repositories_will_use_apt_get_to_update_all_repositories(self):
        self._mock_os_util.execute = Mock()
        
        self._test_object.update_repositories()
        
        self._mock_os_util.execute.assert_called_once_with(["sudo", "apt-get", "update"])


    def test_download_all_packages_will_use_apt_get_to_download_all_files_to_the_given_directory(self):
        self._mock_os_util.execute = Mock()
        
        self._test_object.download_all_packages(self._test_directory)
        
        self._mock_os_util.execute.assert_called_once_with(
                                   ["sudo", "apt-get", 
                                    "-y", "-d", "-o", "Dir::Cache::Archives=" + self._test_directory, 
                                    "install", "endless*"])

    def test_download_all_packages_will_remove_any_file_that_is_in_the_given_directory(self):
        open(os.path.join(self._test_directory, "some_file.txt"), "w").close()
        
        self._mock_os_util.execute = Mock()
        
        self._test_object.download_all_packages(self._test_directory)
        
        self.assertEquals(0, len(os.listdir(self._test_directory)))

    def test_download_all_packages_will_remove_any_directory_that_is_in_the_given_directory(self):
        os.makedirs(os.path.join(self._test_directory, "sub_directory"))
        open(os.path.join(self._test_directory, "sub_directory", "some_file.txt"), "w").close()
        
        self._mock_os_util.execute = Mock()
        
        self._test_object.download_all_packages(self._test_directory)
        
        self.assertEquals(0, len(os.listdir(self._test_directory)))


