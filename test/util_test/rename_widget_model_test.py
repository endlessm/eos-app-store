import unittest

from mock import Mock

from util.rename_widget_model import RenameWidgetModel

class RenameWidgetModelTest(unittest.TestCase):
    def setUp(self):
        self._mock_caller = Mock()

        self._test_object = RenameWidgetModel(self._mock_caller)

    def test_original_name_is_the_identifier_of_the_caller(self):
        original_name = 'this is the original name'
        self._mock_caller._identifier = original_name

        self.assertEquals(original_name, self._test_object.get_original_name())

    def test_save_renames_the_shortcut(self):
        new_name = 'this is the new name'

        self._test_object.save(new_name)

        self._mock_caller.rename_shortcut.assert_called_once_with(new_name)
