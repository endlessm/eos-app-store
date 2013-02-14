import unittest
from datetime import datetime
from mock import Mock

from metrics.time_provider import TimeProvider
from metrics_collection.application_usage_metric import ApplicationUsageMetric

class ApplicationUsageMetricTest(unittest.TestCase):
    def test_to_json_returns_serialized_json(self):
        time_provider = Mock()
        expected_timestamp = TimeProvider().get_current_time()
        time_provider.get_current_time = Mock(return_value=expected_timestamp)
        test_object = ApplicationUsageMetric("app1", 12345, time_provider)

        json_dict = test_object.to_json_dict()
        self.assertEquals(json_dict["activityName"], "app1")
        self.assertEquals(json_dict["timeSpentInActivity"], 12345)
        self.assertEquals(json_dict["timestamp"], expected_timestamp)
