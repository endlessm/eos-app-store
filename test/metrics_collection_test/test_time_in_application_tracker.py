import unittest
from mock import Mock

from metrics_collection.time_in_application_tracker import TimeInApplicationTracker

class TimeInApplicationTrackerTest(unittest.TestCase):
    def setUp(self):
        self._test_object = TimeInApplicationTracker()

    def test_initially_get_app_usages_returns_an_empty_dictionary(self):
        self.assertEquals({}, self._test_object.get_app_usages())

    def test_get_app_usages_returns_updated_usages(self):
        self._test_object.update_app_usage("app1", 123)
        self._test_object.update_app_usage("app2", 234)

        app_usages = self._test_object.get_app_usages()

        self.assertEquals(2, len(app_usages))
        self.assertEquals(app_usages["app1"], 123)
        self.assertEquals(app_usages["app2"], 234)

    def test_updating_usage_has_cumulative_effect(self):
        self._test_object.update_app_usage("app1", 100)
        self._test_object.update_app_usage("app2", 200)
        self._test_object.update_app_usage("app3", 60)
        self._test_object.update_app_usage("app2", 30)
        self._test_object.update_app_usage("app1", 50)

        app_usages = self._test_object.get_app_usages()

        self.assertEquals(3, len(app_usages))
        self.assertEquals(app_usages["app1"], 150)
        self.assertEquals(app_usages["app2"], 230)
        self.assertEquals(app_usages["app3"], 60)


    def test_updating_usage_has_cumulative_effect(self):
        self._test_object.update_app_usage("app1", 100)
        self._test_object.update_app_usage("app2", 200)

        self._test_object.clear_tracking_data()

        self._test_object.update_app_usage("app3", 60)
        self._test_object.update_app_usage("app2", 30)
        self._test_object.update_app_usage("app1", 50)

        app_usages = self._test_object.get_app_usages()

        self.assertEquals(3, len(app_usages))
        self.assertEquals(app_usages["app1"], 50)
        self.assertEquals(app_usages["app2"], 30)
        self.assertEquals(app_usages["app3"], 60)
