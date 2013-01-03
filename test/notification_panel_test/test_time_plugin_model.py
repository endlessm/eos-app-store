import unittest
import datetime
from mock import Mock

from notification_panel.time_display_plugin_model import TimeDisplayPluginModel

class TimePluginModelTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_locale_util = Mock()
        self._test_object = TimeDisplayPluginModel(self._mock_locale_util)
        self._origin_now = datetime.datetime.now
        datetime.datetime = Mock()

    def tearDown(self):
        datetime.datetime.now = self._origin_now

    def test_get_date_text_is_uppercase_text_from_locale_util(self):
        return_text = "this is some text"
        self._mock_locale_util.format_date_time = Mock(return_value=return_text)

        self.assertEquals(return_text.upper(), self._test_object.get_date_text())

    def format_date_time_side_effect(self, given_date):
        self._given_date = given_date
        return ""

    def test_get_date_text_gives_the_current_date_to_the_locale_util(self):
        current_time = Mock()
        datetime.datetime.now = Mock(return_value=current_time)
        self._mock_locale_util.format_date_time = Mock(side_effect=self.format_date_time_side_effect)

        self._test_object.get_date_text()

        self.assertEquals(current_time, self._given_date)

