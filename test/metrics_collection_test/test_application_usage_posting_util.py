import unittest
from mock import Mock
from collections import OrderedDict

from metrics.time_provider import TimeProvider
from metrics_collection.application_usage_posting_util import ApplicationUsagePostingUtil

class ApplicationUsagePostingUtilTest(unittest.TestCase):
    def setUp(self):
        self._mock_tracker = Mock()
        self._mock_usage_sender = Mock()
        self._mock_time_provider = Mock()
        self._test_object = ApplicationUsagePostingUtil(self._mock_tracker, self._mock_usage_sender, self._mock_time_provider)

    def test_when_send_data_is_invoked_currently_saved_data_is_sent(self):
        app1 = "app1"
        app2 = "app2"
        app3 = "app3"

        app1_time = 123
        app2_time = 234
        app3_time = 345

        timestamps= [111,222,333]
        def side_effect():
            return timestamps.pop()
        self._mock_time_provider.get_current_time=Mock(side_effect = timestamps)

        usage_data = OrderedDict()
        usage_data[app1] = app1_time
        usage_data[app2] = app2_time
        usage_data[app3] = app3_time

        def get_usage_data():
            return usage_data
        self._mock_tracker.get_app_usages = get_usage_data

        expected_dict = [{"activityName": "app1", "timeSpentInActivity": 123, "timestamp": 111}, \
                        {"activityName": "app2", "timeSpentInActivity": 234, "timestamp": 222}, \
                        {"activityName": "app3", "timeSpentInActivity": 345, "timestamp": 333}]

        self._test_object.collect_and_send_data()

        self._mock_usage_sender.send_data.assert_called_once_with(expected_dict)

    def test_after_sending_json_tracking_data_is_cleared(self):
        self._mock_tracker.get_app_usages = Mock(return_value = {})

        self._test_object.collect_and_send_data()

        self.assertTrue(self._mock_tracker.clear_tracking_data.called)



