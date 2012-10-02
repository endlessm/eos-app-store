import unittest
from mock import Mock

from notification_panel.all_settings_model import AllSettingsModel

class TestAllSettingsModel(unittest.TestCase):
    def test_get_current_version_uses_output_from_command_line_result(self):
        current_version = "version from desktop"

        mock_os_util = Mock()
        mock_os_util.get_version = Mock(return_value=current_version)

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")

        self.assertEquals(current_version, test_object.get_current_version())

    def test_when_using_command_line_ensure_that_the_correct_command_is_used(self):
        mock_os_util = Mock()
        mock_os_util.execute = Mock(return_value="EndlessOS")

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")

        test_object.get_current_version()

        mock_os_util.get_version.assert_called_once()

    def test_when_update_is_called_we_launch_updates(self):
        mock_app_launcher= Mock()
        server_endpoint = "given server endpoint"
        
        mock_endpoint_provider = Mock()
        mock_endpoint_provider.get_server_endpoint = Mock(return_value=server_endpoint)

        test_object = AllSettingsModel(None, mock_endpoint_provider, mock_app_launcher)
        test_object.update_software()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.UPDATE_COMMAND)

    def test_get_version_delegates_to_os_util(self):
        mock_os_util = Mock()
        mock_os_util.get_version = Mock(return_value="whatever")
        
        test_object = AllSettingsModel(mock_os_util, None, None)
        self.assertEqual("whatever", test_object.get_current_version())

    def test_when_restart_is_called_we_launch_restart(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt", mock_app_launcher)
        test_object.restart()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.RESTART_COMMAND)

    def test_when_logout_is_called_we_launch_logout(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt", mock_app_launcher)
        test_object.logout()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.LOGOUT_COMMAND)

    def test_when_shutdown_is_called_we_launch_shutdown(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt", mock_app_launcher)
        test_object.shutdown()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SHUTDOWN_COMMAND)

    def test_when_settings_is_called_we_launch_settings(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()

        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt", mock_app_launcher)
        test_object.open_settings()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SETTINGS_COMMAND)
