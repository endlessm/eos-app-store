import unittest
from mock import Mock

from metrics.time_provider import TimeProvider
from metrics_collection.application_usage_posting_util import ApplicationUsagePostingUtil

class ApplicationUsagePostingUtilTest(unittest.TestCase):
    def setUp(self):
        self._mock_tracker = Mock()
        self._mock_send_process = Mock()
        self._test_object = ApplicationUsagePostingUtil(self._mock_tracker, self._mock_send_process)

    def test_when_send_data_is_invoked_currently_saved_data_is_sent(self):
        self._test_object.collect_and_send_data()


        


