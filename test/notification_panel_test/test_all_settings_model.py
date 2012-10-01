import unittest
from subprocess import Popen
from mock import Mock

from notification_panel.all_settings_model import AllSettingsModel

class TestAllSettingsModel(unittest.TestCase):
    def test_when_update_is_called_we_launch_updates(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()
        mock_version_provider = Mock()

        test_object = AllSettingsModel(mock_os_util, mock_version_provider, mock_app_launcher)
        test_object.update_software()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.UPDATE_COMMAND)

    def test_when_restart_is_called_we_launch_restart(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()
        mock_version_provider = Mock()

        test_object = AllSettingsModel(mock_os_util, mock_version_provider, mock_app_launcher)
        test_object.restart()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.RESTART_COMMAND)

    def test_when_logout_is_called_we_launch_logout(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()
        mock_version_provider = Mock()

        test_object = AllSettingsModel(mock_os_util, mock_version_provider, mock_app_launcher)
        test_object.logout()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.LOGOUT_COMMAND)

    def test_when_shutdown_is_called_we_launch_shutdown(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()
        mock_version_provider = Mock()

        test_object = AllSettingsModel(mock_os_util, mock_version_provider, mock_app_launcher)
        test_object.shutdown()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SHUTDOWN_COMMAND)

    def test_when_settings_is_called_we_launch_settings(self):
        mock_os_util = Mock()
        mock_app_launcher= Mock()
        mock_version_provider = Mock()

        test_object = AllSettingsModel(mock_os_util, mock_version_provider, mock_app_launcher)
        test_object.open_settings()

        mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SETTINGS_COMMAND)
