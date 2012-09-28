import unittest
from subprocess import Popen
from mock import Mock

from notification_panel.all_settings_model import AllSettingsModel

class TestAllSettingsModel(unittest.TestCase):
    def test_get_current_version_shows_whatever_is_in_version_file(self):
        test_file = "/tmp/test_file.txt"
        current_version = "endless os version"

        with open(test_file, "w") as f:
            f.write(current_version)

        test_object = AllSettingsModel(None, test_file)

        self.assertEquals(current_version, test_object.get_current_version())

    def test_get_current_version_uses_output_from_command_line_result(self):
        current_version = "version from browser"

        mock_os_util = Mock()
        mock_os_util.execute = Mock(return_value=current_version)

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")

        self.assertEquals("EndlessOS " + current_version, test_object.get_current_version())

    def test_when_using_command_line_ensure_that_the_correct_command_is_used(self):
        mock_os_util = Mock()
        mock_os_util.execute = Mock(return_value="")

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")

        test_object.get_current_version()

        mock_os_util.execute.assert_called_once_with(AllSettingsModel.VERSION_COMMAND)

    def test_when_using_command_line_and_an_error_occurs_then_just_display_endlessos(self):
        mock_os_util = Mock()
        mock_os_util.execute = Mock(side_effect=Exception("boom!"))

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")

        self.assertEquals("EndlessOS", test_object.get_current_version())

