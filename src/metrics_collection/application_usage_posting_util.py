import json

from metrics.time_provider import TimeProvider
from application_usage_sender import ApplicationUsageSender
from application_usage_metric import ApplicationUsageMetric

class ApplicationUsagePostingUtil():
    def __init__(self, app_tracker, usage_sender=ApplicationUsageSender(), time_provider = TimeProvider()):
        self._app_tracker = app_tracker
        self._usage_sender = usage_sender
        self._time_provider = time_provider

    def collect_and_send_data(self):
        usage_data = self._app_tracker.get_app_usages()
        usage_metrics = [ ApplicationUsageMetric(app, usage_data[app], self._time_provider) for app in usage_data] 

        json_items = [ json_item.to_json_dict() for json_item in usage_metrics] 

        self._usage_sender.send_data({'time_in_activities' : json_items})

        self._app_tracker.clear_tracking_data()
