import unittest
from mock import Mock, call #@UnresolvedImport

import shutil
import os
from startup.auto_updates.endless_downloader import EndlessDownloader
from startup.auto_updates import endpoint_provider

class EndlessDownloaderTestCase(unittest.TestCase):
    _test_directory = "/tmp/updater_test_dir"
    
    def setUp(self):
        self._orig_endpoint_provider = endpoint_provider.get_endless_url

        shutil.rmtree(self._test_directory, True)
        os.makedirs(self._test_directory)
        
        self._mock_file_synchronizer = Mock()
        self._mock_file_downloader = Mock()

        self._test_object = EndlessDownloader(self._mock_file_downloader, self._mock_file_synchronizer)

    def tearDown(self):
        endpoint_provider.get_endless_url = self._orig_endpoint_provider

    def test_remote_file_list_is_saved_as_new_current_files_list(self):
        remote_file_content = "this is the remote file content"
        self._mock_file_downloader.download_file = Mock(return_value=remote_file_content)
        self._mock_file_synchronizer.files_to_download = Mock(return_value=[])

        self._test_object.download_all_packages(self._test_directory)

        with open(os.path.join(self._test_directory, "files.txt"), "r") as f:
            local_file_content = f.read()

        self.assertEquals(remote_file_content, local_file_content)

    def test_give_files_file_to_file_synchronizer(self):
        remote_file_content = "this is the remote file content"
        open(os.path.join(self._test_directory, "file1.txt"), "w").close()
        open(os.path.join(self._test_directory, "file2.txt"), "w").close()
        open(os.path.join(self._test_directory, "file3.txt"), "w").close()

        self._mock_file_downloader.download_file = Mock(return_value=remote_file_content)

        self._mock_file_synchronizer.files_to_download = Mock(return_value=[])

        self._test_object.download_all_packages(self._test_directory)

        self._mock_file_synchronizer.files_to_download.assert_called_once_with(
                                            ["file1.txt", "file2.txt", "file3.txt"], remote_file_content)

    def test_correct_files_are_being_downloaded(self):
        endpoint = "endpoint"
        endpoint_provider.get_endless_url = Mock(return_value=endpoint)
        list_of_files = [("file1", "md5sum1"), ("file2", "md5sum2"), ("file3", "md5sum3")]
        self._mock_file_synchronizer.files_to_download = Mock(return_value=list_of_files)
        
        self._mock_file_downloader.download_file = Mock(return_value="")
        
        self._test_object.download_all_packages(self._test_directory)
        expected_calls = [call(endpoint + "/mirror/files.txt"), 
		  						call(endpoint + "/mirror/file1", "md5sum1"), 
								call(endpoint + "/mirror/file2", "md5sum2"), 
								call(endpoint + "/mirror/file3", "md5sum3")]

        self.assertEquals(expected_calls, self._mock_file_downloader.download_file.call_args_list)

    def test_downloaded_files_go_to_correct_directory(self):
        endpoint = "endpoint"
        endpoint_provider.get_endless_url = Mock(return_value=endpoint)
        
        self._mock_file_synchronizer.files_to_download = Mock(return_value=[("file1", "md5sum1"), ("file2", "md5sum2"), ("file3", "md5sum3")])

        def side_effect(*args, **kwargs):
            if args[0] == endpoint + "/mirror/file1":
                return "file 1 content"
            elif args[0] == endpoint + "/mirror/file2":
                return "file 2 content"
            elif args[0] == endpoint + "/mirror/file3":
                return "file 3 content"
            elif args[0] == endpoint + "/mirror/files.txt":
                return "list of files content"
        self._mock_file_downloader.download_file = Mock(side_effect=side_effect)

        self._test_object.download_all_packages(self._test_directory)

        with open(os.path.join(self._test_directory, "file1"), "r") as f:
            self.assertEquals("file 1 content", f.read())
        with open(os.path.join(self._test_directory, "file2"), "r") as f:
            self.assertEquals("file 2 content", f.read())
        with open(os.path.join(self._test_directory, "file3"), "r") as f:
            self.assertEquals("file 3 content", f.read())
    
#    def test_when_an_exception_occurs_downloading_a_file_???????(self):
#        pass

