import unittest
from mock import Mock
from notification_panel.all_settings_presenter import AllSettingsPresenter

class AllSettingsPresenterTest(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()

    def test_initially_display_the_view(self):
        AllSettingsPresenter(self._mock_view, self._mock_model)

        self._mock_view.display.assert_called_once_with()

    def test_initially_set_the_current_version_from_the_model(self):
        current_version = "this is the current version"
        self._mock_model.get_current_version = Mock(return_value=current_version)

        AllSettingsPresenter(self._mock_view, self._mock_model)

        self._mock_view.set_current_version.assert_called_once_with(current_version)
