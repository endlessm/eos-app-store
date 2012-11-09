import unittest
import md5

from mock import Mock #@UnresolvedImport
from uuid import uuid4

from startup.auto_updates.file_downloader import FileDownloader

class FileDownloaderTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_web_connection = Mock()
        self._test_object = FileDownloader(self._mock_web_connection)

    def test_download_file_returns_file_from_location_if_md5_matches(self):
        location = Mock()
        expected_content = uuid4().get_urn()
        self._mock_web_connection.get = Mock(return_value = expected_content) 
        md5sum = md5.new(expected_content).hexdigest()
        
        self.assertIsNotNone(md5sum)
        
        actual_content = self._test_object.download_file(location, md5sum)

        self.assertEquals(expected_content, actual_content)
        self._mock_web_connection.get.assert_called_once_with(location)
        
    def test_download_file_returns_file_from_location_if_first_attemt_fails(self):
        expected_content = uuid4().get_urn()
        location = Mock()
        
        contents= [ expected_content, "something_else"]
        def mock_get(url):
            if location == url: 
                return contents.pop()
        
        self._mock_web_connection.get = mock_get 
        md5sum = md5.new(expected_content).hexdigest()
        
        actual_content = self._test_object.download_file(location, md5sum)

        self.assertEquals(expected_content, actual_content)
        
    def test_download_file_throws_exception_if_we_cant_get_the_file_in_max_number_of_retries(self):
        expected_content = uuid4().get_urn()
        location = Mock()
        
        contents= [ expected_content ]
        for index in range(self._test_object.MAX_RETRIES): #@UnusedVariable
            contents.append(uuid4().get_urn())
            
        def mock_get(url):
            if location == url: 
                return contents.pop()
        
        self._mock_web_connection.get = mock_get 
        md5sum = md5.new(expected_content).hexdigest()
        
        self.failUnlessRaises(Exception, self._test_object.download_file, location, md5sum)
            
    def test_when_expected_md5sum_is_none_dont_check_it(self):
        location = Mock()
        expected_content = uuid4().get_urn()
        self._mock_web_connection.get = Mock(return_value = expected_content) 
        
        actual_content = self._test_object.download_file(location)

        self.assertEquals(expected_content, actual_content)
        self._mock_web_connection.get.assert_called_once_with(location)       

        
