import json
from datetime import datetime 

from metrics.time_provider import TimeProvider
class ApplicationUsageMetric():
    def __init__(self, application, total_time, time_provider = TimeProvider()):
        self._time_stamp = time_provider.get_current_time()
        self._application = application
        self._total_time = total_time

    def to_json_dict(self):
        return {'activityName':self._application, 'timeSpentInActivity': self._total_time, 'timestamp': self._time_stamp}
