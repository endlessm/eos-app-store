import unittest

from startup.auto_updates.file_synchronizer import FileSynchronizer

class FileSynchronizerTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = FileSynchronizer()

    def test_local_has_nothing_then_return_all_remote_files(self):
        local = ""
        remote = "test1.txt\ntest2.txt\ntest3.txt\n"

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals(["test1.txt", "test2.txt", "test3.txt"], to_download)

    def test_local_some_then_return_other_remote_files(self):
        local = "test2.txt\n"
        remote = "test1.txt\ntest2.txt\ntest3.txt\n"

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals(["test1.txt", "test3.txt"], to_download)

    def test_edge_case_of_empty_remote(self):
        local = "test1.txt\ntest2.txt\n"
        remote = ""

        to_download = self._test_object.files_to_download(local, remote)

        self.assertEquals([], to_download)
