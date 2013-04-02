class TimeInApplicationTracker():
    def __init__(self):
        self._tracking_data = {}

    def update_app_usage(self, application, time):
        if application not in self._tracking_data:
            self._tracking_data[application] = time
        else:
            self._tracking_data[application] += time

    def get_app_usages(self):
        return self._tracking_data

    def clear_tracking_data(self):
        self._tracking_data.clear()
