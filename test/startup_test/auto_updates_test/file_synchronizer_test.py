import unittest

from startup.auto_updates.file_synchronizer import FileSynchronizer

class FileSynchronizerTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = FileSynchronizer()
        self._test_directory = "/tmp"

    def test_local_has_nothing_then_return_all_remote_files(self):
        local = []
        remote = " abcdef test1.txt\nbcdefg    test2.txt \ncdefgh\ttest3.txt\n"

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals(3, len(to_download))
        self.assertTrue(("test1.txt", "abcdef") in to_download)
        self.assertTrue(("test2.txt", "bcdefg") in to_download)
        self.assertTrue(("test3.txt", "cdefgh") in to_download)

    def test_local_some_then_return_other_remote_files(self):
        local = ["test2.txt"]
        remote = "abcdef test1.txt\nbcdefg test2.txt\ncdefgh test3.txt\n"

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals(2, len(to_download))
        self.assertTrue(("test1.txt", "abcdef") in to_download)
        self.assertTrue(("test3.txt", "cdefgh") in to_download)

    def test_edge_case_of_empty_remote(self):
        local = ["test1.txt", "test2.txt"]
        remote = ""

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals([], to_download)
