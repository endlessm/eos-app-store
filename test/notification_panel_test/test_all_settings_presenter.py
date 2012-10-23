import unittest
from mock import Mock
from notification_panel.all_settings_view import AllSettingsView
from notification_panel.all_settings_presenter import AllSettingsPresenter

class AllSettingsPresenterTest(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()
        self._mock_background_chooser = Mock()

        self._mock_view.add_listener = Mock(side_effect=self._view_add_listener)

    def _view_add_listener(self, *args, **kwargs):
        if args[0] == AllSettingsView.DESKTOP_BACKGROUND:
            self._desktop_listener = args[1]
        elif args[0] == AllSettingsView.UPDATE_SOFTWARE:
            self._update_software_listener = args[1]
        elif args[0] == AllSettingsView.SETTINGS:
            self._settings_listener = args[1]
        elif args[0] == AllSettingsView.LOGOUT:
            self._logout_listener = args[1]
        elif args[0] == AllSettingsView.RESTART:
            self._restart_listener = args[1]
        elif args[0] == AllSettingsView.SHUTDOWN:
            self._shutdown_listener = args[1]

    def test_initially_display_the_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._mock_view.display.assert_called_once_with()

    def test_initially_set_the_current_version_from_the_model(self):
        current_version = "this is the current version"
        self._mock_model.get_current_version = Mock(return_value=current_version)

        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._mock_view.set_current_version.assert_called_once_with(current_version)

    def test_only_update_software_when_user_confirms(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
#        self._mock_view.confirm = Mock(return_value=True)

        self._update_software_listener()

        self._mock_model.update_software.assert_called_once_with()

    def test_only_logout_when_user_confirms(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=True)

        self._logout_listener()

        self._mock_model.logout.assert_called_once_with()

    def test_dont_logout_when_user_does_not_confirm(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=False)

        self._logout_listener()

        self.assertFalse(self._mock_model.logout.called)

    def test_only_shutdown_when_user_confirms(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=True)

        self._shutdown_listener()

        self._mock_model.shutdown.assert_called_once_with()

    def test_dont_shutdown_when_user_does_not_confirm(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=False)

        self._shutdown_listener()

        self.assertFalse(self._mock_model.shutdown.called)

    def test_only_restart_when_user_confirms(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=True)

        self._restart_listener()

        self._mock_model.restart.assert_called_once_with()

    def test_dont_restart_when_user_does_not_confirm(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)
        self._mock_view.confirm = Mock(return_value=False)

        self._restart_listener()

        self.assertFalse(self._mock_model.restart.called)

    def test_when_restarting_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._restart_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_shutdown_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._shutdown_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_logout_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._logout_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_settings_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._settings_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_updating_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._update_software_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_changing_background_hide_window_on_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._desktop_listener()

        self._mock_view.hide_window.assert_called_once_with()

    def test_when_changing_background_create_a_background_chooser(self):
        AllSettingsPresenter(self._mock_view, self._mock_model, self._mock_background_chooser)

        self._desktop_listener()

        self._mock_background_chooser.launch.assert_called_once_with(self._mock_view)

