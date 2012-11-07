import unittest
from startup.beatbox_tasks import BeatboxTasks
from startup.beatbox_tasks import Folder

from mock import Mock
from mock import call
import shutil
import os
import os.path


class BeatboxTaskIntegrationTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/originating")
        open("/tmp/originating/test.music", "w").close()
        open("/tmp/originating/test2.music", "w").close()
        os.makedirs("/tmp/destination")

        home_path_provider = Mock()
        home_path_provider.get_user_directory = Mock(return_value="/tmp/destination")
        os_util = Mock()
        os_util.execute = Mock()
        self.task = BeatboxTasks("/tmp/originating/*", home_path_provider, os_util)

    def tearDown(self):
        shutil.rmtree("/tmp/originating", True)
        shutil.rmtree("/tmp/destination", True)

    def test_copying_files(self):
        self.task.execute()
        self.assertTrue(os.path.isfile("/tmp/destination/test.music"))
        self.assertTrue(os.path.isfile("/tmp/destination/test2.music"))

class FolderTest(unittest.TestCase):
    def setUp(self):
        self.globber = Mock()
        self.path = Mock()

    def test_copy_files_to(self):
        file1 = Mock()
        file2 = Mock()
        self.globber =  Mock(return_value=[file1, file2])

        test_object = Folder(self.path, self.globber)

        destination_folder = Mock()
        destination_folder.add_file = Mock()

        test_object.copy_files_to(destination_folder)

        self.globber.assert_was_called_once_with(self.path)
        destination_folder.add_file.assert_was_called_once_with(file1)
        destination_folder.add_file.assert_was_called_once_with(file2)

    def test_add_file(self):
        copier = Mock()
        test_object = Folder(self.path, self.globber, copier)

        file_path = Mock()

        test_object.add_file(file_path)

        copier.assert_was_called_once_with(file_path, self.path)

    def test_file_paths(self):
        file_collection = Mock()
        self.globber =  Mock(return_value=file_collection)

        test_object = Folder(self.path, self.globber)

        self.assertEquals(file_collection, test_object.file_paths())
        self.globber.assert_was_called_once_with(self.path)
