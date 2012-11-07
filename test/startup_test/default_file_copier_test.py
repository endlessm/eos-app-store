import unittest
from startup.default_file_copier import DefaultFileCopier

from mock import Mock
from mock import call
import shutil
import os
import os.path


class DefaultFileCopierTest(unittest.TestCase):
    def setUp(self):
        self.destination_path = "dest_path"
        self.copier = Mock()
        self.test_object = DefaultFileCopier(self.destination_path,
                self.copier)

    def test_homepath_provider_is_used_to_call_copy_tree(self):
        self.test_source = "source"
        self.test_object.copy_in(self.test_source)

        self.copier.assert_called_once_with(self.test_source,
                self.destination_path)
